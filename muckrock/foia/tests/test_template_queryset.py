"""
Tests for the FOIATemplateQuerySet
"""

# Django
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

# Third Party
import pytest

# MuckRock
from muckrock.core.factories import AgencyFactory, UserFactory
from muckrock.foia.factories import FOIATemplateFactory
from muckrock.foia.models import FOIATemplate
from muckrock.jurisdiction.factories import (
    FederalJurisdictionFactory,
    StateJurisdictionFactory,
)


class TestFOIATemplateQuerySet(TestCase):
    """Test the FOIATemplateQuerySet methods"""

    def setUp(self):
        """Set up tests"""
        self.user = UserFactory(
            first_name="John", last_name="Doe", profile__full_name="John Doe"
        )
        self.jurisdiction = StateJurisdictionFactory(
            name="Massachusetts",
            law__shortname="MPRL",
        )
        self.agency = AgencyFactory(jurisdiction=self.jurisdiction)

        # Create templates with different scopes
        self.generic_template = FOIATemplateFactory(
            jurisdiction=None,
            template=(
                "To Whom It May Concern:\r\n\r\nPursuant to the "
                "{ law name }, I hereby request the following "
                "records:\r\n\r\n{ requested docs }\r\n\r\n"
                "{ waiver }\r\n\r\nThank you.\r\n\r\n{ name }"
            ),
        )
        self.jurisdiction_template = FOIATemplateFactory(
            jurisdiction=self.jurisdiction,
            template=(
                "Dear { agency name }:\r\n\r\nPursuant to the "
                "{ short name }, I hereby request:\r\n\r\n"
                "{ requested docs }\r\n\r\n{ waiver }\r\n\r\n{ name }"
            ),
        )

    @pytest.mark.django_db
    def test_render_single_agency_with_jurisdiction_template(self):
        """Test rendering template for a single agency with jurisdiction-
        specific template
        """

        requested_docs = "All emails from January 2024"
        result = FOIATemplate.objects.render([self.agency], self.user, requested_docs)

        # Should use jurisdiction template since it's more specific
        assert "Dear" in result
        assert self.agency.name in result
        assert "MPRL" in result
        assert requested_docs in result
        assert self.jurisdiction.waiver in result
        assert "John Doe" in result

    @pytest.mark.django_db
    def test_render_single_agency_fallback_to_generic(self):
        """Test rendering falls back to generic template when no
        jurisdiction template exists
        """

        # Create agency with jurisdiction that has no template
        other_jurisdiction = StateJurisdictionFactory(
            name="Vermont", law__name="Vermont Public Records Act"
        )
        other_agency = AgencyFactory(jurisdiction=other_jurisdiction)

        requested_docs = "Budget documents for 2024"
        result = FOIATemplate.objects.render([other_agency], self.user, requested_docs)

        # Should use generic template
        assert "To Whom It May Concern" in result
        assert "Vermont Public Records Act" in result
        assert requested_docs in result

    @pytest.mark.django_db
    def test_render_single_agency_fallback_to_parent_jurisdiction(self):
        """Test rendering falls back to parent jurisdiction template when
        specific jurisdiction has none
        """

        # Create parent and child jurisdictions
        parent_jurisdiction = FederalJurisdictionFactory()
        child_jurisdiction = StateJurisdictionFactory(
            name="New Jersey",
            parent=parent_jurisdiction,
        )
        child_agency = AgencyFactory(jurisdiction=child_jurisdiction)

        # Create template only for parent
        FOIATemplateFactory(
            jurisdiction=parent_jurisdiction,
            template=(
                "Federal request:\r\n\r\n" "{ requested docs }\r\n\r\n{ closing }"
            ),
        )

        requested_docs = "All correspondence"
        result = FOIATemplate.objects.render([child_agency], self.user, requested_docs)

        assert "Federal request" in result
        assert requested_docs in result

    @pytest.mark.django_db
    def test_render_multiple_agencies_generic(self):
        """Test rendering template for multiple agencies uses generic
        rendering
        """

        agency2 = AgencyFactory()
        requested_docs = "All records related to Project X"
        result = FOIATemplate.objects.render(
            [self.agency, agency2], self.user, requested_docs
        )

        # Should use generic template for multiple agencies
        assert "To Whom It May Concern" in result
        # Generic rendering should not include specific agency name
        # when not in HTML mode
        assert result == self.generic_template.template

    @pytest.mark.django_db
    def test_render_with_jurisdiction_only(self):
        """Test rendering template with jurisdiction parameter only (no
        agency)
        """

        requested_docs = "Meeting minutes from 2024"
        result = FOIATemplate.objects.render(
            [], self.user, requested_docs, jurisdiction=self.jurisdiction
        )

        # Should render using jurisdiction template
        assert "Dear { agency name }" in result
        assert "MPRL" in result
        assert requested_docs in result

    @pytest.mark.django_db
    def test_render_with_edited_boilerplate(self):
        """Test rendering with edited_boilerplate creates temporary
        template
        """

        custom_text = "Custom request text:\n\n{ agency name }"
        result = FOIATemplate.objects.render(
            [self.agency],
            self.user,
            custom_text,
            edited_boilerplate=True,
        )

        # Should use the custom text as-is (requested_docs in this case is
        # the custom text)
        assert result == custom_text.replace("{ agency name }", self.agency.name)

    @pytest.mark.django_db
    def test_render_with_split(self):
        """Test rendering with split parameter splits at $split$ marker"""

        requested_docs = "Documents from 2024"
        result = FOIATemplate.objects.render(
            [self.agency], self.user, requested_docs, split=True
        )

        # Should return a tuple/list with split content
        assert isinstance(result, list)
        assert len(result) == 2
        # First part should be before the requested docs
        assert "Dear" in result[0]
        # Second part should be after
        assert self.jurisdiction.waiver in result[1]

    @pytest.mark.django_db
    def test_render_with_anonymous_user(self):
        """Test rendering template with anonymous user doesn't include user
        info
        """

        anonymous = AnonymousUser()
        requested_docs = "Public information"
        result = FOIATemplate.objects.render([self.agency], anonymous, requested_docs)

        # Should not include user name since user is not authenticated
        assert "John Doe" not in result
        # But should include other template content
        assert requested_docs in result
        assert "MPRL" in result

    @pytest.mark.django_db
    def test_render_with_proxy_user(self):
        """Test rendering template with a proxy user"""

        proxy_user = UserFactory(
            first_name="Jane", last_name="Smith", profile__full_name="Jane Smith"
        )
        requested_docs = "Records for 2024"
        result = FOIATemplate.objects.render(
            [self.agency],
            self.user,
            requested_docs,
            proxy=proxy_user,
        )

        # Should include proxy user information
        assert "Jane Smith" in result
        assert "citizen of" in result
        # Should mention coordination with original user if different
        if proxy_user != self.user:
            assert "John Doe" in result
            assert "in coordination with" in result

    @pytest.mark.django_db
    def test_render_generic_html_mode(self):
        """Test generic rendering in HTML mode includes tooltips"""

        agency2 = AgencyFactory()
        requested_docs = "Test documents"
        result = FOIATemplate.objects.render(
            [self.agency, agency2], self.user, requested_docs, html=True
        )

        # HTML mode should include abbr tags with tooltips
        assert '<abbr class="tooltip"' in result
        assert "{ law name }" in result or "{ agency name }" in result

    @pytest.mark.django_db
    def test_render_single_with_html_mode(self):
        """Test single agency rendering in HTML mode"""

        requested_docs = "Test documents"
        result = FOIATemplate.objects.render(
            [self.agency], self.user, requested_docs, html=True
        )

        # Should still render properly and replace tags
        assert requested_docs in result
        assert self.agency.name in result or "{ agency name }" in result

    @pytest.mark.django_db
    def test_render_empty_agencies_no_jurisdiction(self):
        """Test rendering with no agencies and no jurisdiction parameter"""

        requested_docs = "Generic request"
        result = FOIATemplate.objects.render([], self.user, requested_docs)

        # Should use generic template
        assert result == self.generic_template.template

    @pytest.mark.django_db
    def test_render_no_templates_exist(self):
        """Test rendering when no templates exist returns None"""

        # Delete all templates
        FOIATemplate.objects.all().delete()

        requested_docs = "Test request"
        result = FOIATemplate.objects.render([self.agency], self.user, requested_docs)

        assert result is None

    @pytest.mark.django_db
    def test_render_respects_template_ordering(self):
        """Test that templates are selected by pk ordering"""

        # Create another generic template (will have higher pk)
        FOIATemplateFactory(
            jurisdiction=None,
            template="Second generic template: { requested docs }",
        )

        requested_docs = "Test documents"
        # Delete jurisdiction template to ensure we use generic
        self.jurisdiction_template.delete()
        agency = AgencyFactory()

        result = FOIATemplate.objects.render([agency], self.user, requested_docs)

        # Should use first template by pk (the original generic_template)
        assert "To Whom It May Concern" in result
