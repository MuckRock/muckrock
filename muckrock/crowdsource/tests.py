# -*- coding: utf-8 -*-
"""Tests for the crowdsource app"""

# Django
from django.test import TestCase

# Standard Library
import json
from datetime import datetime

# Third Party
from nose.tools import assert_false, assert_is_none, eq_, ok_

# MuckRock
from muckrock.crowdsource.factories import (
    CrowdsourceDataFactory,
    CrowdsourceFactory,
    CrowdsourceResponseFactory,
    CrowdsourceSelectFieldFactory,
    CrowdsourceTextFieldFactory,
    CrowdsourceValueFactory,
)
from muckrock.factories import UserFactory


class TestCrowdsource(TestCase):
    """Test the Crowdsource model"""

    def test_get_data_to_show(self):
        """Get data to show should pick the correct data"""
        crowdsource = CrowdsourceFactory()
        assert_is_none(crowdsource.get_data_to_show(crowdsource.user))
        data = CrowdsourceDataFactory(crowdsource=crowdsource)
        eq_(data, crowdsource.get_data_to_show(crowdsource.user))

    def test_create_form(self):
        """Create form should create fields from the JSON"""
        crowdsource = CrowdsourceFactory()
        CrowdsourceTextFieldFactory(
            crowdsource=crowdsource,
            label='Delete Me',
            order=0,
        )
        crowdsource.create_form(
            json.dumps([
                {
                    'label': 'Text Field',
                    'type': 'text',
                    'description': 'Here is some help',
                },
                {
                    'label':
                        'Select Field',
                    'type':
                        'select',
                    'values': [
                        {
                            'label': 'Choice 1',
                            'value': 'choice-1',
                        },
                        {
                            'label': 'Choice 2',
                            'value': 'choice-2',
                        },
                    ],
                },
            ])
        )
        assert_false(crowdsource.fields.filter(label='Delete Me').exists())
        ok_(
            crowdsource.fields.filter(
                label='Text Field',
                type='text',
                help_text='Here is some help',
                order=0,
            ).exists()
        )
        ok_(
            crowdsource.fields.filter(
                label='Select Field',
                type='select',
                order=1,
            ).exists()
        )
        eq_(crowdsource.fields.get(label='Select Field').choices.count(), 2)

    def test_uniqify_label_name(self):
        """Uniqify label name should give each label a unqiue name"""
        # pylint: disable=protected-access
        crowdsource = CrowdsourceFactory()
        seen = set()
        eq_('one', crowdsource._uniqify_label_name(seen, 'one'))
        eq_('one-1', crowdsource._uniqify_label_name(seen, 'one'))
        eq_('two', crowdsource._uniqify_label_name(seen, 'two'))
        eq_('one-2', crowdsource._uniqify_label_name(seen, 'one'))
        eq_('two-1', crowdsource._uniqify_label_name(seen, 'two'))

    def test_get_form_json(self):
        """Get the JSON to rebuild the form builder"""
        crowdsource = CrowdsourceFactory()
        CrowdsourceTextFieldFactory(
            crowdsource=crowdsource,
            label='Text Field',
            help_text='Help',
            order=0,
        )
        CrowdsourceSelectFieldFactory(
            crowdsource=crowdsource,
            label='Select Field',
            order=1,
        )
        form_data = json.loads(crowdsource.get_form_json())
        eq_(form_data[0]['type'], 'text')
        eq_(form_data[0]['label'], 'Text Field')
        eq_(form_data[0]['description'], 'Help')

        eq_(form_data[1]['type'], 'select')
        eq_(form_data[1]['label'], 'Select Field')
        eq_(len(form_data[1]['values']), 3)
        eq_(
            set(form_data[1]['values'][0].keys()),
            {'value', 'label'},
        )

    def test_get_header_values(self):
        """Get the header values for CSV export"""
        crowdsource = CrowdsourceFactory()
        CrowdsourceTextFieldFactory(
            crowdsource=crowdsource,
            label='Text Field',
            help_text='Help',
            order=0,
        )
        CrowdsourceSelectFieldFactory(
            crowdsource=crowdsource,
            label='Select Field',
            order=1,
        )
        eq_(
            crowdsource.get_header_values(['meta']),
            ['user', 'datetime', 'skip', 'Text Field', 'Select Field'],
        )
        crowdsource.multiple_per_page = True
        eq_(
            crowdsource.get_header_values(['meta']),
            [
                'user', 'datetime', 'skip', 'number', 'Text Field',
                'Select Field'
            ],
        )
        CrowdsourceDataFactory(crowdsource=crowdsource)
        eq_(
            crowdsource.get_header_values(['meta']),
            [
                'user', 'datetime', 'skip', 'number', 'datum', 'meta',
                'Text Field', 'Select Field'
            ],
        )

    def test_get_metadata_keys(self):
        """Get the metadata keys associated with this crowdsoucre's data"""
        crowdsource = CrowdsourceFactory()
        eq_(crowdsource.get_metadata_keys(), [])
        data = CrowdsourceDataFactory(crowdsource=crowdsource)
        eq_(crowdsource.get_metadata_keys(), [])
        data.metadata = {'foo': 'bar', 'muck': 'rock'}
        data.save()
        eq_(set(crowdsource.get_metadata_keys()), {'foo', 'muck'})


class TestCrowdsourceData(TestCase):
    """Test the Crowdsource Data model"""

    def test_get_choices(self):
        """Test the get choices queryset method"""
        crowdsource = CrowdsourceFactory()
        data = CrowdsourceDataFactory.create_batch(
            3,
            crowdsource=crowdsource,
        )
        user = crowdsource.user
        limit = 2

        # all data should be valid choices
        eq_(
            set(crowdsource.data.get_choices(limit, user)),
            set(data),
        )
        # if I respond to one, it is no longer a choice for me
        CrowdsourceResponseFactory(
            crowdsource=crowdsource,
            user=crowdsource.user,
            data=data[0],
        )
        eq_(
            set(crowdsource.data.get_choices(limit, user)),
            set(data[1:]),
        )
        # if one has at least `limit` responses, it is no longer a valid choice
        CrowdsourceResponseFactory.create_batch(
            2,
            crowdsource=crowdsource,
            data=data[1],
        )
        eq_(
            set(crowdsource.data.get_choices(limit, user)),
            set(data[2:]),
        )
        # multiple responses from the same user only count once
        new_user = UserFactory()
        CrowdsourceResponseFactory.create_batch(
            2,
            crowdsource=crowdsource,
            data=data[2],
            user=new_user,
        )
        eq_(
            set(crowdsource.data.get_choices(limit, user)),
            set(data[2:]),
        )


class TestCrowdsourceResponse(TestCase):
    """Test the Crowdsource Response model"""

    def test_get_values(self):
        """Test getting the values from the response"""
        crowdsource = CrowdsourceFactory()
        response = CrowdsourceResponseFactory(
            crowdsource=crowdsource,
            user__username='Username',
            datetime=datetime(2017, 1, 2),
            data=None,
        )
        field = CrowdsourceTextFieldFactory(
            crowdsource=crowdsource,
            order=0,
        )
        CrowdsourceValueFactory(
            response=response,
            field=field,
            value='Value',
        )

        eq_(
            response.get_values([]),
            ['Username', '2017-01-02 00:00:00', False, 'Value'],
        )
