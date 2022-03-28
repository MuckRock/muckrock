"""
FOIATemplate allows users to create their own request template language

These can be shared among organizations or specified as the defaults
for certain jurisdictions or agencies
"""

# Django
from django.contrib.auth.models import User
from django.db import models

# MuckRock
from muckrock.foia.querysets import FOIATemplateQuerySet


def make_tag(tag, title):
    """Make a tooltip tag for an html template placeholder"""
    return (tag, f'<abbr class="tooltip" title="{title}">{tag}</abbr>')


class FOIATemplate(models.Model):
    """A custom template for public records request language"""

    name = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="templates")
    jurisdiction = models.ForeignKey(
        "jurisdiction.Jurisdiction",
        related_name="templates",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    template = models.TextField()

    objects = FOIATemplateQuerySet.as_manager()

    class Meta:
        verbose_name = "FOIA Template"

    def __str__(self):
        return self.name

    def _handle_users(self, tags, user, jurisdiction, **kwargs):
        """Handle user names and proxies"""
        if kwargs.get("html"):
            tags.append(make_tag("{ name }", "This will be replaced by your full name"))
        elif user.is_authenticated:
            tags.append(("{ name }", user.profile.full_name))

        proxy = kwargs.get("proxy")
        if kwargs.get("html"):
            tags.append(
                make_tag(
                    "{ closing }",
                    "This will be replaced by a suitable closing for the letter",
                )
            )
        elif proxy:
            jurisdiction_name = (
                jurisdiction.legal.name if jurisdiction else "{ jurisdiction }"
            )
            coordination_clause = (
                ""
                if proxy == user
                else f", in coordination with {user.profile.full_name}"
            )
            tags.append(
                (
                    "{ closing }",
                    f"This request is filed by {proxy.profile.full_name}, a citizen of "
                    f"{jurisdiction_name}{coordination_clause}.",
                )
            )
        elif user.is_authenticated:
            tags.append(("{ closing }", f"Sincerely,\n\n{user.profile.full_name}"))

    def render(self, agency, user, requested_docs, **kwargs):
        """Render this template for a given agency"""
        template = self.template
        jurisdiction = kwargs.pop(
            "jurisdiction", agency.jurisdiction if agency else None
        )
        tags = [
            ("{ law name }", jurisdiction.get_law_name()),
            ("{ short name }", jurisdiction.get_law_name(abbrev=True)),
            ("{ days }", jurisdiction.get_days()),
            ("{ waiver }", jurisdiction.get_waiver()),
            ("{ requested docs }", requested_docs),
        ]
        if agency:
            tags.append(("{ agency name }", agency.name))

        self._handle_users(tags, user, jurisdiction, **kwargs)

        for tag, replace in tags:
            template = template.replace(tag, str(replace))
        return template

    def render_generic(self, user, requested_docs, **kwargs):
        """Render this template in a generic manner"""
        if not kwargs.get("html"):
            return self.template

        template = self.template

        tags = [
            make_tag(
                "{ law name }", "This will be replaced by the relevant transparency law"
            ),
            make_tag(
                "{ short name }",
                "This will be replaced by the abbreviation for the "
                "relevant transparency law",
            ),
            make_tag(
                "{ days }",
                "Number of says statue requires or default of 10 days if no requirement",
            ),
            make_tag(
                "{ agency name }", "This will be replaced by the name of the agency"
            ),
            make_tag(
                "{ waiver }",
                "This will be replaced by jurisdiction approriate fee waiver language "
                "if available, or generic fee waiver language otherwise",
            ),
            ("{ requested docs }", requested_docs),
        ]

        self._handle_users(tags, user, None, **kwargs)

        for tag, replace in tags:
            template = template.replace(tag, str(replace))
        return template
