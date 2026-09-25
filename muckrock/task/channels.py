# -*- coding: utf-8 -*-
"""
The channel layer for review agency tasks

A channel is one of an agency's communication mailboxes.  The agency is the
container; the channel is the primitive.  This module answers, for one agency:
what are its real mailboxes, which are broken, how are they broken, and how
much live traffic each is blocking.  The queue, the agency detail view and the
repair form all read the same answer from here, so they cannot disagree.

Channel identity is the EmailAddress row.  There is deliberately no
case-normalizing logic here: the merge_email_addresses command already made one
row equal one mailbox, and a surviving case variant is a data bug for that
command to fix rather than something this layer should hide.
"""

# Django
from django.db.models import Count, Max
from django.utils import timezone

# Standard Library
from dataclasses import dataclass, field

# MuckRock
from muckrock.communication.models import EmailAddress, EmailError
from muckrock.task.constants import REVIEW_AGENCY_FOLLOWUP

# An error flag with no bounce event in two years tells you something different
# from a live breakage: the flag is probably stale and the channel is a lower
# triage priority.  61% of error flags on the affected agencies are this shape.
STALE_ERROR_DAYS = 730

# How many recent error events to carry per channel.  100% of recent errors are
# permanent failures and 71% are SMTP 550, so the latest few carry the whole
# signal -- staff need the code and reason, not a twenty row scroll.
RECENT_ERROR_LIMIT = 5

# Sender side reputation failures.  No address swap fixes these, so they must be
# distinguishable from a dead mailbox -- they are a different job.
REPUTATION_REASONS = frozenset(["blacklisted", "espblock"])

# SMTP codes in plain language.  A staffer triaging the queue needs to know
# what broke, not to decode a number -- and 71% of these are a 550.
SMTP_CODE_MEANINGS = {
    "550": "Mailbox does not exist",
    "551": "Mailbox not local",
    "552": "Mailbox full",
    "553": "Address rejected as invalid",
    "554": "Delivery refused",
    "450": "Mailbox temporarily unavailable",
    "451": "Temporary local failure",
    "452": "Temporarily out of storage",
    "421": "Service temporarily unavailable",
}

# Reasons that describe our own sending reputation rather than the recipient.
# These read differently on purpose: no address swap fixes them.
REPUTATION_MESSAGES = {
    "blacklisted": "Blocked by recipient -- our sending address is blacklisted",
    "espblock": "Blocked by recipient -- sender reputation, not a bad address",
}

# Domains that belong to FOIA portals rather than to agency mailboxes.  These
# are portal notification senders that got harvested from inbound mail and then
# used as outbound targets.  PORTAL_TYPES carries type slugs, not domains, so
# there is nothing to derive from it -- this map is necessarily explicit.
PORTAL_DOMAINS = frozenset(
    [
        "mycusthelp.net",
        "securerelease.us",
        "foiaonline.gov",
        "nextrequest.com",
        "mail.foia.state.gov",
        "govqa.us",
        "justfoia.com",
        "foiadirect.com",
    ]
)

# Local parts we should never be mailing.  These were harvested from inbound
# mail and then used as outbound targets; the repair is to point back at the
# agency's real mailbox, not to invent a new address.
NOREPLY_PREFIXES = (
    "noreply",
    "no-reply",
    "no_reply",
    "donotreply",
    "do-not-reply",
    "do_not_reply",
    "postmaster",
    "mailer-daemon",
    "notification",
    "notifications",
)


def classify_address(address, newest_reason=""):
    """How is this channel broken, and therefore how is it repaired?

    Conflating the failure classes is what makes the current UI unhelpful: a
    portal notification address invites an email swap that is actively wrong,
    and a reputation block invites an address swap that cannot help.

    Takes the newest error's reason rather than the error rows, so the queue
    can classify from an annotation without loading any errors.

    Classification is display only.  It never triggers a repair action.
    """
    domain = address.domain.lower()
    if any(
        domain == portal or domain.endswith("." + portal) for portal in PORTAL_DOMAINS
    ):
        # Checked before no-reply on purpose: many portal senders are literally
        # named no-reply, and "portal" is the answer that stops a wrong repair.
        return "portal"

    local = address.local.lower()
    if local.startswith(NOREPLY_PREFIXES):
        return "noreply"

    if newest_reason in REPUTATION_REASONS:
        return "reputation"

    return "dead"


def classify_channel(address, errors=()):
    """Classify a channel from its loaded error rows

    Only the newest error decides.  An old reputation block must not mask a
    mailbox that is dead now.
    """
    newest = _newest_error(errors)
    return classify_address(address, newest.reason if newest else "")


def _newest_error(errors):
    """The most recent error event, from an already loaded collection"""
    errors = [error for error in errors if error is not None]
    if not errors:
        return None
    return max(errors, key=lambda error: error.datetime)


@dataclass
class Channel:
    """One of an agency's communication mailboxes"""

    address: EmailAddress
    blocked_count: int = 0
    is_primary: bool = False
    classification: str = "dead"
    has_error: bool = False
    last_error: object = None
    last_error_code: str = ""
    last_error_reason: str = ""
    last_confirm: object = None
    last_open: object = None
    error_count: int = 0
    foias: list = field(default_factory=list)
    recent_errors: list = field(default_factory=list)

    @property
    def is_active(self):
        """Is this channel carrying live traffic?

        An active channel is one requests are actually routed to, not merely an
        address with a stale error flag on its roster link.  Counting every
        flagged link doubles the apparent size of the problem.
        """
        return self.blocked_count > 0

    @property
    def is_portal(self):
        """Is email the wrong repair tool for this channel?"""
        return self.classification == "portal"

    @property
    def last_error_age(self):
        """Days since the last error event, or None if there is none"""
        if self.last_error is None:
            return None
        return (timezone.now() - self.last_error).days

    @property
    def last_error_message(self):
        """The last error in plain language

        The reason is checked first: a reputation block is a different job
        from a dead mailbox, and reading it as one would send a staffer after
        a replacement address that cannot help.
        """
        if self.last_error_reason in REPUTATION_MESSAGES:
            return REPUTATION_MESSAGES[self.last_error_reason]
        if not self.last_error_code:
            return ""
        code = str(self.last_error_code)
        if code in SMTP_CODE_MEANINGS:
            return "%s (SMTP %s)" % (SMTP_CODE_MEANINGS[code], code)
        return "SMTP %s" % code

    @property
    def is_stale_error(self):
        """Flagged as broken, but nothing has bounced in two years"""
        age = self.last_error_age
        return age is not None and age > STALE_ERROR_DAYS


def agency_channels(agency):
    """Build the channel roster for one agency, most blocked first

    Deliberately a constant number of queries regardless of channel count: the
    heaviest agency has 23 channels and the roster is rendered per page view.
    """
    # Every address the agency is linked to, however the link is flagged...
    links = {
        link.email_id: link for link in agency.agencyemail_set.select_related("email")
    }
    # ...plus any address open requests are actually routed to, which can
    # include one the roster never listed.
    open_requests = list(
        agency.foiarequest_set.get_open()
        .exclude(email=None)
        .select_related("agency__jurisdiction", "composer", "email")
    )

    addresses = {link.email_id: link.email for link in links.values()}
    foias_by_address = {}
    for foia in open_requests:
        addresses.setdefault(foia.email_id, foia.email)
        foias_by_address.setdefault(foia.email_id, []).append(foia)

    if not addresses:
        return []

    primary_ids = {
        link.email_id
        for link in links.values()
        if link.request_type == "primary" and link.email_type == "to"
    }

    stats = _address_stats(addresses)
    errors_by_address = _recent_errors(addresses)

    channels = []
    for address_id, address in addresses.items():
        recent_errors = errors_by_address.get(address_id, [])
        newest = _newest_error(recent_errors)
        stat = stats.get(address_id)
        channels.append(
            Channel(
                address=address,
                blocked_count=len(foias_by_address.get(address_id, [])),
                is_primary=address_id in primary_ids,
                classification=classify_channel(address, recent_errors),
                has_error=address.status == "error",
                last_error=getattr(stat, "last_error", None),
                last_error_code=newest.code if newest else "",
                last_error_reason=newest.reason if newest else "",
                last_confirm=getattr(stat, "last_confirm", None),
                last_open=getattr(stat, "last_open", None),
                error_count=getattr(stat, "error_count", 0) or 0,
                foias=foias_by_address.get(address_id, []),
                recent_errors=recent_errors,
            )
        )

    channels.sort(key=lambda channel: (-channel.blocked_count, channel.address.email))
    return channels


# Pinned so a test can assert the roster cost does not grow with channel count.
# Bump it deliberately, never to make a failing assertion pass.
agency_channels.__query_count__ = 4


def _address_stats(addresses):
    """Per address error and delivery stats, in one pass

    Annotated separately from the request query to keep the joins bounded --
    the same shape the old get_review_data() used, for the same reason.
    """
    return (
        EmailAddress.objects.filter(pk__in=addresses)
        .annotate(
            error_count=Count("errors", distinct=True),
            last_error=Max("errors__datetime"),
            last_confirm=Max("to_emails__confirmed_datetime"),
            last_open=Max("opens__datetime"),
        )
        .in_bulk()
    )


def _recent_errors(addresses):
    """The most recent error events per address

    Fetched newest first across all the addresses at once and then trimmed in
    Python: a per address slice would be a query per channel.
    """
    errors = (
        EmailError.objects.filter(recipient__in=addresses)
        .order_by("-datetime")
        .only("recipient", "datetime", "code", "error", "event", "reason")
    )
    by_address = {}
    for error in errors:
        bucket = by_address.setdefault(error.recipient_id, [])
        if len(bucket) < RECENT_ERROR_LIMIT:
            bucket.append(error)
    return by_address


def agency_rollup(agency, channels=None):
    """The agency level scorecard

    total_blocked is the impact number and drives priority.  The roster shape
    counts sit beside it precisely so a long channel list cannot be mistaken
    for urgency.
    """
    if channels is None:
        channels = agency_channels(agency)

    last_success = max(
        (c.last_confirm for c in channels if c.last_confirm is not None),
        default=None,
    )
    return {
        "total_blocked": sum(c.blocked_count for c in channels),
        "channels_known": len(channels),
        "channels_broken": sum(1 for c in channels if c.has_error),
        "channels_active": sum(1 for c in channels if c.is_active),
        "channels_portal": sum(1 for c in channels if c.is_portal),
        "has_portal_channel": any(c.is_portal for c in channels),
        "last_success": last_success,
    }


def serialize_channels(agency, channels=None):
    """The channel roster as plain data for the repair component

    The component receives everything as props and makes no fetches of its
    own, so this is the whole contract between the view and the UI.  Keep it
    flat and JSON safe.
    """
    if channels is None:
        channels = agency_channels(agency)
    rollup = agency_rollup(agency, channels=channels)

    return {
        "agency": {
            "id": agency.pk,
            "name": agency.name,
            "jurisdiction": str(agency.jurisdiction),
            "url": agency.get_absolute_url(),
        },
        "total_blocked": rollup["total_blocked"],
        "channels_known": rollup["channels_known"],
        "channels_broken": rollup["channels_broken"],
        "channels_active": rollup["channels_active"],
        "has_portal_channel": rollup["has_portal_channel"],
        "last_success": _isoformat(rollup["last_success"]),
        "channels": [_serialize_channel(channel) for channel in channels],
        # The follow-up starts from the legacy task's text rather than blank
        "default_reply": REVIEW_AGENCY_FOLLOWUP,
    }


def _serialize_channel(channel):
    """One channel as plain data"""
    return {
        "id": channel.address.pk,
        "email": channel.address.email,
        "name": channel.address.name,
        "blocked_count": channel.blocked_count,
        "is_primary": channel.is_primary,
        "is_active": channel.is_active,
        "has_error": channel.has_error,
        "classification": channel.classification,
        # Carried explicitly so the component never has to reimplement the
        # rule that email repair is the wrong tool for a portal address.
        "is_portal": channel.is_portal,
        "repairable_by_email": not channel.is_portal,
        "last_error": _isoformat(channel.last_error),
        "last_error_age": channel.last_error_age,
        "last_error_code": str(channel.last_error_code or ""),
        "last_error_reason": channel.last_error_reason,
        "last_error_message": channel.last_error_message,
        "is_stale_error": channel.is_stale_error,
        "error_count": channel.error_count,
        "last_confirm": _isoformat(channel.last_confirm),
        "recent_errors": [
            {
                "datetime": _isoformat(error.datetime),
                "code": str(error.code or ""),
                "reason": error.reason,
                "error": error.error,
            }
            for error in channel.recent_errors
        ],
        "foias": [
            {
                "id": foia.pk,
                "title": foia.title,
                "status": foia.get_status_display(),
                "url": foia.get_absolute_url(),
            }
            for foia in channel.foias
        ],
    }


def _isoformat(value):
    """A datetime as an ISO string, or None"""
    return value.isoformat() if value is not None else None
