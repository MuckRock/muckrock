# -*- coding: utf-8 -*-
"""
Lowercase every email address and merge the rows that collide as a result

One real mailbox should be one EmailAddress row.  Before the local part was
normalized, the same mailbox accumulated case-sensitive rows. Every consumer of
an email address (a request's contact, the error history, the review agency task
queue) treats a row as a mailbox, so we merge these split rows.

Run with --dry-run first.  The plan it prints is the review artifact.
"""

# Django
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from django.db.models.functions import Lower

# Standard Library
import sys
from collections import defaultdict, namedtuple

# MuckRock
from muckrock.communication.models import EmailAddress

# Most specific first -- used to pick the surviving AgencyEmail link when
# collapsing duplicate (agency, email) rows.
REQUEST_TYPE_RANK = ["primary", "appeal", "none"]
EMAIL_TYPE_RANK = ["to", "cc", "none"]


# One mailbox's rows, the survivor already chosen, plus the reference weights
# that chose it -- carried together so the report and the merge agree.
Group = namedtuple("Group", ["canonical_pk", "pks", "weights", "breakdown"])


def _rank(value, ranking):
    """Position in a precedence list, unknown values sorting last"""
    try:
        return ranking.index(value)
    except ValueError:
        return len(ranking)


class Command(BaseCommand):
    """Lowercase and merge colliding email addresses"""

    help = (
        "Lowercase every EmailAddress and merge the rows that collide. "
        "Use --dry-run to print the plan without writing."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be merged without writing anything",
        )

    def handle(self, *args, **options):
        # pylint: disable=broad-except
        dry_run = options["dry_run"]

        groups = self._find_collisions()
        self.stdout.write(f"{len(groups)} mailbox(es) split across multiple rows")

        merged = 0
        failed = 0
        for group in groups:
            try:
                self._report_group(group)
                if not dry_run:
                    self._merge_group(group.canonical_pk, group.pks)
                merged += 1
            except Exception as exc:
                failed += 1
                self.stderr.write(
                    self.style.ERROR(
                        f"Failed to merge group {group.canonical_pk}: {exc}"
                    )
                )
                self.stderr.write(repr(sys.exc_info()[1]))

        # Rows with no collision still need their stored casing fixed.  This is
        # separate from the merge: nothing has to move, only the value changes.
        lowercased = self._lowercase_remaining(dry_run)

        verb = "would merge" if dry_run else "merged"
        self.stdout.write(
            self.style.SUCCESS(
                f"{verb} {merged} group(s), {failed} failed, "
                f"{lowercased} non-colliding row(s) lowercased"
            )
        )

    def _find_collisions(self):
        """Every group of rows for one mailbox, with the survivor chosen

        Which spelling the survivor happens to carry does not matter, because
        EmailAddress.save() lowercases it on the way out; this command needs
        no canonical-spelling logic of its own.
        """
        colliding = (
            EmailAddress.objects.annotate(lowered=Lower("email"))
            .values("lowered")
            .annotate(count=Count("pk"))
            .filter(count__gt=1)
            .values_list("lowered", flat=True)
        )
        groups = []
        for lowered in colliding:
            pks = list(
                EmailAddress.objects.annotate(lowered=Lower("email"))
                .filter(lowered=lowered)
                .order_by("pk")
                .values_list("pk", flat=True)
            )
            weights, breakdown = self._reference_counts(pks)
            groups.append(
                Group(
                    canonical_pk=self._pick_canonical(weights),
                    pks=pks,
                    weights=weights,
                    breakdown=breakdown,
                )
            )
        return groups

    @staticmethod
    def _pick_canonical(weights):
        """The row the most other rows already point at

        Reference count measures how established a row actually is, where pk
        age only proxies for it: the heaviest row is the one the rest of the
        system is really using.  Keeping it also means the fewest references
        have to move, which shrinks each transaction and the surface where a
        PROTECT failure can bite.

        Ties fall back to the lowest pk so the choice never depends on row
        ordering -- otherwise a dry-run report could stop predicting the real
        run.
        """
        return max(weights, key=lambda pk: (weights[pk], -pk))

    def _reference_counts(self, pks):
        """Rows pointing at each address, in total and per relation

        One query per relation, feeding both the canonical choice and the
        dry-run report rather than being counted twice.
        """
        weights = dict.fromkeys(pks, 0)
        breakdown = {}
        for rel in self._repointable_relations():
            field_name = rel.field.name
            rows = (
                rel.related_model.objects.filter(**{f"{field_name}__in": pks})
                .values(field_name)
                .annotate(count=Count("pk", distinct=True))
            )
            counts = {row[field_name]: row["count"] for row in rows}
            if counts:
                breakdown[f"{rel.related_model._meta.label}.{field_name}"] = counts
            for pk, count in counts.items():
                weights[pk] += count
        return weights, breakdown

    def _report_group(self, group):
        """Print what will happen to one group

        The report is the review artifact, so it names the weight behind the
        choice: a bare "keeping pk=N" cannot be reviewed.
        """
        addresses = EmailAddress.objects.in_bulk(group.pks)
        canonical = addresses[group.canonical_pk]
        losers = [addresses[pk] for pk in group.pks if pk != group.canonical_pk]
        self.stdout.write(
            f"  {canonical.email.lower()}: keeping pk={group.canonical_pk} "
            f"({canonical.email!r}, "
            f"{group.weights[group.canonical_pk]} reference(s)), removing "
            + ", ".join(
                f"pk={a.pk} ({a.email!r}, {group.weights[a.pk]} reference(s))"
                for a in losers
            )
        )
        for relation, counts in group.breakdown.items():
            moving = sum(
                count for pk, count in counts.items() if pk != group.canonical_pk
            )
            if moving:
                self.stdout.write(f"      {relation}: {moving} row(s) to repoint")

    @staticmethod
    def _repointable_relations():
        """Every relation that has to move, discovered from the model

        Discovered rather than hardcoded so a relation added later cannot be
        silently skipped.  M2M relations that go through an explicit through
        model are excluded -- their through model's own FK is in this list, and
        repointing that is what actually moves the link.
        """
        relations = []
        for rel in EmailAddress._meta.related_objects:
            if rel.field.many_to_many:
                through = rel.field.remote_field.through
                if through is not None and not through._meta.auto_created:
                    continue
            relations.append(rel)
        return relations

    def _merge_group(self, canonical_pk, pks):
        """Merge one group of case variants

        One transaction per group, with the delete strictly after every
        repoint.  PROTECT on four of these FKs is the safety net: a missed
        repoint refuses to delete rather than orphaning a reference.
        """
        loser_pks = [pk for pk in pks if pk != canonical_pk]
        with transaction.atomic():
            addresses = EmailAddress.objects.select_for_update().in_bulk(pks)
            canonical = addresses[canonical_pk]
            losers = [addresses[pk] for pk in loser_pks]

            self._resolve_fields(canonical, losers)
            self._collapse_agency_emails(canonical, loser_pks)

            for rel in self._repointable_relations():
                if rel.field.many_to_many:
                    self._repoint_m2m(rel, canonical, loser_pks)
                else:
                    self._repoint_fk(rel, canonical, loser_pks)

            # Ordering is load bearing: repoint first so PROTECT is satisfied,
            # delete the losers next so their rows stop occupying the lowercased
            # address, and only then save the canonical row -- whose save()
            # lowercases it into the value a loser just vacated.
            EmailAddress.objects.filter(pk__in=loser_pks).delete()
            canonical.save()

    @staticmethod
    def _resolve_fields(canonical, losers):
        """Merge the scalar fields onto the surviving row

        status is error if any member errored -- a mailbox that bounces under
        one spelling bounces under all of them.  name takes the first non
        blank, preferring the canonical row's.
        """
        if any(a.status == "error" for a in [canonical] + losers):
            canonical.status = "error"
        if not canonical.name:
            for loser in losers:
                if loser.name:
                    canonical.name = loser.name
                    break

    @staticmethod
    def _collapse_agency_emails(canonical, loser_pks):
        """Collapse duplicate (agency, email) links, keeping the most specific

        Done before the generic FK repoint because AgencyEmail has no unique
        constraint to lean on: repointing blindly would leave an agency with
        several links to the same address.
        """
        # pylint: disable=import-outside-toplevel
        # MuckRock
        from muckrock.agency.models import AgencyEmail

        links = list(AgencyEmail.objects.filter(email__in=[canonical.pk] + loser_pks))
        by_agency = defaultdict(list)
        for link in links:
            by_agency[link.agency_id].append(link)

        for agency_links in by_agency.values():
            agency_links.sort(
                key=lambda link: (
                    _rank(link.request_type, REQUEST_TYPE_RANK),
                    _rank(link.email_type, EMAIL_TYPE_RANK),
                    link.pk,
                )
            )
            survivor, duplicates = agency_links[0], agency_links[1:]
            if survivor.email_id != canonical.pk:
                survivor.email = canonical
                survivor.save()
            if duplicates:
                AgencyEmail.objects.filter(
                    pk__in=[link.pk for link in duplicates]
                ).delete()

    @staticmethod
    def _repoint_fk(rel, canonical, loser_pks):
        """Point a foreign key at the surviving row"""
        rel.related_model.objects.filter(**{f"{rel.field.name}__in": loser_pks}).update(
            **{rel.field.name: canonical}
        )

    @staticmethod
    def _repoint_m2m(rel, canonical, loser_pks):
        """Move M2M links to the surviving row, deduping as we go

        A row that held two variants must end with one entry, not two.
        """
        model = rel.related_model
        field_name = rel.field.name
        holders = model.objects.filter(**{f"{field_name}__in": loser_pks}).distinct()
        for holder in holders:
            manager = getattr(holder, field_name)
            manager.remove(*loser_pks)
            manager.add(canonical)

    def _lowercase_remaining(self, dry_run):
        """Lowercase rows that need no merge, reporting how many"""
        remaining = EmailAddress.objects.exclude(email=Lower("email"))
        count = remaining.count()
        if count and not dry_run:
            remaining.update(email=Lower("email"))
        return count
