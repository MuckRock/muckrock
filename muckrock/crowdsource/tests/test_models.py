# -*- coding: utf-8 -*-
"""Tests for crowdsource models"""

# Django
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.utils import timezone

# Standard Library
import json
from datetime import datetime

# MuckRock
from muckrock.core.factories import ProjectFactory, UserFactory
from muckrock.crowdsource.factories import (
    CrowdsourceCheckboxGroupFieldFactory,
    CrowdsourceDataFactory,
    CrowdsourceFactory,
    CrowdsourceHeaderFieldFactory,
    CrowdsourceResponseFactory,
    CrowdsourceSelectFieldFactory,
    CrowdsourceTextFieldFactory,
    CrowdsourceValueFactory,
)
from muckrock.crowdsource.models import Crowdsource


class TestCrowdsource(TestCase):
    """Test the Crowdsource model"""

    def test_get_data_to_show(self):
        """Get data to show should pick the correct data"""
        crowdsource = CrowdsourceFactory()
        ip_address = None
        assert crowdsource.get_data_to_show(crowdsource.user, ip_address) is None
        data = CrowdsourceDataFactory(crowdsource=crowdsource)
        assert data == crowdsource.get_data_to_show(crowdsource.user, ip_address)

    def test_create_form(self):
        """Create form should create fields from the JSON"""
        crowdsource = CrowdsourceFactory()
        CrowdsourceTextFieldFactory(crowdsource=crowdsource, label="Delete Me", order=0)
        crowdsource.create_form(
            json.dumps(
                [
                    {
                        "label": "Text Field",
                        "type": "text",
                        "description": "Here is some help",
                    },
                    {
                        "label": "Select Field",
                        "type": "select",
                        "values": [
                            {"label": "Choice 1", "value": "choice-1"},
                            {"label": "Choice 2", "value": "choice-2"},
                        ],
                    },
                ]
            )
        )
        assert crowdsource.fields.get(label="Delete Me").deleted
        assert crowdsource.fields.filter(
            label="Text Field", type="text", help_text="Here is some help", order=0
        ).exists()
        assert crowdsource.fields.filter(
            label="Select Field", type="select", order=1
        ).exists()
        assert crowdsource.fields.get(label="Select Field").choices.count() == 2

    def test_uniqify_label_name(self):
        """Uniqify label name should give each label a unqiue name"""
        # pylint: disable=protected-access
        crowdsource = CrowdsourceFactory()
        seen = set()
        assert "one" == crowdsource._uniqify_label_name(seen, "one")
        assert "one-1" == crowdsource._uniqify_label_name(seen, "one")
        assert "two" == crowdsource._uniqify_label_name(seen, "two")
        assert "one-2" == crowdsource._uniqify_label_name(seen, "one")
        assert "two-1" == crowdsource._uniqify_label_name(seen, "two")

    def test_get_form_json(self):
        """Get the JSON to rebuild the form builder"""
        crowdsource = CrowdsourceFactory()
        CrowdsourceTextFieldFactory(
            crowdsource=crowdsource, label="Text Field", help_text="Help", order=0
        )
        CrowdsourceSelectFieldFactory(
            crowdsource=crowdsource, label="Select Field", order=1
        )
        form_data = json.loads(crowdsource.get_form_json())
        assert form_data[0]["type"] == "text"
        assert form_data[0]["label"] == "Text Field"
        assert form_data[0]["description"] == "Help"

        assert form_data[1]["type"] == "select"
        assert form_data[1]["label"] == "Select Field"
        assert len(form_data[1]["values"]) == 3
        assert set(form_data[1]["values"][0].keys()) == {"value", "label"}

    def test_get_header_values(self):
        """Get the header values for CSV export"""
        crowdsource = CrowdsourceFactory()
        CrowdsourceTextFieldFactory(
            crowdsource=crowdsource, label="Text Field", help_text="Help", order=0
        )
        CrowdsourceHeaderFieldFactory(crowdsource=crowdsource, label="Header", order=1)
        CrowdsourceSelectFieldFactory(
            crowdsource=crowdsource, label="Select Field", order=2
        )
        assert crowdsource.get_header_values(["meta"]) == [
            "user",
            "public",
            "datetime",
            "skip",
            "flag",
            "gallery",
            "tags",
            "Text Field",
            "Select Field",
        ]
        crowdsource.multiple_per_page = True
        assert crowdsource.get_header_values(["meta"]) == [
            "user",
            "public",
            "datetime",
            "skip",
            "flag",
            "gallery",
            "tags",
            "number",
            "Text Field",
            "Select Field",
        ]
        CrowdsourceDataFactory(crowdsource=crowdsource)
        assert crowdsource.get_header_values(["meta"]) == [
            "user",
            "public",
            "datetime",
            "skip",
            "flag",
            "gallery",
            "tags",
            "number",
            "datum",
            "meta",
            "Text Field",
            "Select Field",
        ]

    def test_get_metadata_keys(self):
        """Get the metadata keys associated with this crowdsoucre's data"""
        crowdsource = CrowdsourceFactory()
        assert crowdsource.get_metadata_keys() == []
        data = CrowdsourceDataFactory(crowdsource=crowdsource)
        assert crowdsource.get_metadata_keys() == []
        data.metadata = {"foo": "bar", "muck": "rock"}
        data.save()
        assert set(crowdsource.get_metadata_keys()) == {"foo", "muck"}

    def test_get_viewable(self):
        """Get the list of viewable crowdsources for the user"""
        project = ProjectFactory()
        admin = UserFactory(is_staff=True)
        proj_user, owner, user = UserFactory.create_batch(3)
        project.contributors.add(proj_user)

        draft_crowdsource = CrowdsourceFactory(user=owner, status="draft")
        open_crowdsource = CrowdsourceFactory(user=owner, status="open")
        closed_crowdsource = CrowdsourceFactory(user=owner, status="close")
        project_crowdsource = CrowdsourceFactory(
            user=owner, status="open", project=project, project_only=True
        )

        crowdsources = Crowdsource.objects.get_viewable(admin)
        assert draft_crowdsource in crowdsources
        assert open_crowdsource in crowdsources
        assert closed_crowdsource in crowdsources
        assert project_crowdsource in crowdsources

        crowdsources = Crowdsource.objects.get_viewable(proj_user)
        assert draft_crowdsource not in crowdsources
        assert open_crowdsource in crowdsources
        assert closed_crowdsource not in crowdsources
        assert project_crowdsource in crowdsources

        crowdsources = Crowdsource.objects.get_viewable(owner)
        assert draft_crowdsource in crowdsources
        assert open_crowdsource in crowdsources
        assert closed_crowdsource in crowdsources
        assert project_crowdsource in crowdsources

        crowdsources = Crowdsource.objects.get_viewable(user)
        assert draft_crowdsource not in crowdsources
        assert open_crowdsource in crowdsources
        assert closed_crowdsource not in crowdsources
        assert project_crowdsource not in crowdsources

        crowdsources = Crowdsource.objects.get_viewable(AnonymousUser())
        assert draft_crowdsource not in crowdsources
        assert open_crowdsource in crowdsources
        assert closed_crowdsource not in crowdsources
        assert project_crowdsource not in crowdsources


class TestCrowdsourceData(TestCase):
    """Test the Crowdsource Data model"""

    def test_get_choices(self):
        """Test the get choices queryset method"""
        crowdsource = CrowdsourceFactory()
        data = CrowdsourceDataFactory.create_batch(4, crowdsource=crowdsource)
        user = crowdsource.user
        ip_address = "127.0.0.1"
        limit = 2

        # all data should be valid choices
        assert set(crowdsource.data.get_choices(limit, user, None)) == set(data)
        # if I respond to one, it is no longer a choice for me
        CrowdsourceResponseFactory(
            crowdsource=crowdsource, user=crowdsource.user, data=data[0]
        )
        assert set(crowdsource.data.get_choices(limit, user, None)) == set(data[1:])
        # if one has at least `limit` responses, it is no longer a valid choice
        CrowdsourceResponseFactory.create_batch(
            2, crowdsource=crowdsource, data=data[1]
        )
        assert set(crowdsource.data.get_choices(limit, user, None)) == set(data[2:])
        # multiple responses from the same user only count once
        new_user = UserFactory()
        CrowdsourceResponseFactory(
            crowdsource=crowdsource, user=new_user, data=data[2], number=1
        )
        CrowdsourceResponseFactory(
            crowdsource=crowdsource, user=new_user, data=data[2], number=2
        )
        assert set(crowdsource.data.get_choices(limit, user, None)) == set(data[2:])
        # if I anonymously to one, it is no longer a choice for me
        CrowdsourceResponseFactory(
            crowdsource=crowdsource, ip_address=ip_address, data=data[3]
        )
        assert set(crowdsource.data.get_choices(limit, None, ip_address)) == set(
            [data[0], data[2]]
        )


class TestCrowdsourceResponse(TestCase):
    """Test the Crowdsource Response model"""

    def test_get_values(self):
        """Test getting the values from the response"""
        crowdsource = CrowdsourceFactory()
        response = CrowdsourceResponseFactory(
            crowdsource=crowdsource,
            user__username="Username",
            datetime=datetime(2017, 1, 2, tzinfo=timezone.get_current_timezone()),
            data=None,
        )
        field = CrowdsourceTextFieldFactory(crowdsource=crowdsource, order=0)
        CrowdsourceHeaderFieldFactory(crowdsource=crowdsource, order=1)
        CrowdsourceValueFactory(response=response, field=field, value="Value")

        assert response.get_values([]) == [
            "Username",
            False,
            "2017-01-02 00:00:00",
            False,
            False,
            False,
            "",
            "Value",
        ]

    def test_get_values_blank(self):
        """Test getting the values from the response
        Blank responses should only be ignored for multiselect fields
        """
        crowdsource = CrowdsourceFactory()
        response = CrowdsourceResponseFactory(
            crowdsource=crowdsource,
            user__username="Username",
            public=True,
            datetime=datetime(2017, 1, 2, tzinfo=timezone.get_current_timezone()),
            data=None,
        )
        text_field = CrowdsourceTextFieldFactory(crowdsource=crowdsource, order=0)
        CrowdsourceValueFactory(response=response, field=text_field, value="")
        check_field = CrowdsourceCheckboxGroupFieldFactory(
            crowdsource=crowdsource, order=1
        )
        CrowdsourceValueFactory(response=response, field=check_field, value="")
        CrowdsourceValueFactory(response=response, field=check_field, value="Foo")
        CrowdsourceValueFactory(response=response, field=check_field, value="Foo")
        check_field2 = CrowdsourceCheckboxGroupFieldFactory(
            crowdsource=crowdsource, order=2
        )
        CrowdsourceValueFactory(response=response, field=check_field2, value="")

        assert response.get_values([]) == [
            "Username",
            True,
            "2017-01-02 00:00:00",
            False,
            False,
            False,
            "",
            "",
            "Foo, Foo",
            "",
        ]
