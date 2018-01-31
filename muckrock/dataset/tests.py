# -*- coding: utf-8 -*-
"""
Tests for data sets
"""

# pylint: disable=invalid-name

# Django
from django.core.urlresolvers import reverse
from django.test import RequestFactory, TestCase

# Standard Library
import random
from cStringIO import StringIO

# Third Party
from nose.tools import assert_false, assert_true, eq_

# MuckRock
from muckrock.dataset import fields, views
from muckrock.dataset.models import DataField, DataRow, DataSet
from muckrock.factories import UserFactory
from muckrock.test_utils import mock_middleware


class TestDataSetModels(TestCase):
    """Test the data set models"""

    def setUp(self):
        """Create a dataset for each test case"""
        self.user = UserFactory()
        self.dataset = DataSet.objects.create(
            name='Data Set',
            slug='data-set',
            user=self.user,
        )
        for i, name in enumerate('abc'):
            DataField.objects.create(
                dataset=self.dataset,
                name=name,
                slug=name,
                field_number=i,
                type='text',
            )
        data = [
            {
                'a': 'alice',
                'b': '901',
                'c': 'foo'
            },
            {
                'a': 'bob',
                'b': '102',
                'c': 'bar'
            },
            {
                'a': 'charlie',
                'b': '201',
                'c': 'baz'
            },
        ]
        for i, row in enumerate(data):
            DataRow.objects.create(
                dataset=self.dataset,
                row_number=i,
                data=row,
            )

    def test_create_from_csv(self):
        """Test creating a dataset from a csv"""
        csv = StringIO('d,e,f\n' 'doug,24,foo\n' 'eric,45,bar\n' 'fox,62,baz\n')
        dataset = DataSet.objects.create_from_csv(
            'Name',
            self.user,
            csv,
        )
        field_names = dataset.fields.all()
        eq_(['d', 'e', 'f'], [f.name for f in field_names])
        eq_(['choice', 'number', 'choice'], [f.type for f in field_names])
        rows = dataset.rows.all()
        eq_(['doug', 'eric', 'fox'], [r.data['d'] for r in rows])
        eq_(['24', '45', '62'], [r.data['e'] for r in rows])
        eq_(['foo', 'bar', 'baz'], [r.data['f'] for r in rows])

    def test_create_from_csv_repeat_columns(self):
        """Duplicate column names do not crash creation"""
        csv = StringIO(
            'name,age,name\n'
            'doug,24,foo\n'
            'eric,45,bar\n'
            'fox,62,baz\n'
        )
        DataSet.objects.create_from_csv(
            'Name',
            self.user,
            csv,
        )

    def test_detect_field_types(self):
        """Test detecting the field types"""
        self.dataset.detect_field_types()
        field_names = self.dataset.fields.all()
        eq_(['choice', 'number', 'choice'], [f.type for f in field_names])

    def test_choices(self):
        """Test getting the choice options for a choice field"""
        field = self.dataset.fields.get(name='a')
        eq_(set(field.choices()), set(['alice', 'bob', 'charlie']))

    def test_row_sort(self):
        """Test sorting the data"""
        field_names = {f.slug: f for f in self.dataset.fields.all()}
        rows = list(
            self.dataset.rows.sort(
                field_names,
                [{
                    'field': 'b',
                    'dir': 'asc'
                }],
            )
        )
        eq_(rows, sorted(rows, key=lambda x: x.data['b']))
        rows = list(
            self.dataset.rows.sort(
                field_names,
                [{
                    'field': 'a',
                    'dir': 'desc'
                }],
            )
        )
        eq_(rows, sorted(rows, key=lambda x: x.data['a'], reverse=True))

    def test_row_tabulator_filter(self):
        """Test filtering the data"""
        field_names = {f.slug: f for f in self.dataset.fields.all()}
        rows = self.dataset.rows.tabulator_filter(
            field_names,
            [{
                'field': 'a',
                'type': '=',
                'value': 'alice'
            }],
        )
        eq_(len(rows), 1)
        rows = self.dataset.rows.tabulator_filter(
            field_names,
            [
                {
                    'field': 'a',
                    'type': '!=',
                    'value': 'bob'
                },
                {
                    'field': 'c',
                    'type': 'like',
                    'value': 'ba'
                },
            ],
        )
        eq_(len(rows), 1)


class TestDataSetFields(TestCase):
    """Test the data set fields"""

    def test_text_field_validate(self):
        """Test text field validate"""
        assert_true(fields.TextField.validate('anything'))

    def test_multitext_field_validate(self):
        """Test multitext field validate"""
        assert_true(fields.MultiTextField.validate('has a \n newline'))
        assert_false(fields.MultiTextField.validate('has not a newline'))

    def test_number_field_validate(self):
        """Test number field validate"""
        assert_true(fields.NumberField.validate('123'))
        assert_true(fields.NumberField.validate('-123'))
        assert_true(fields.NumberField.validate('12.30'))
        assert_false(fields.NumberField.validate('not a number'))
        assert_false(fields.NumberField.validate('12 not a number'))

    def test_email_field_validate(self):
        """Test email field validate"""
        assert_true(fields.EmailField.validate('admin@example.com'))
        assert_false(fields.EmailField.validate('not an email'))

    def test_url_field_validate(self):
        """Test URL field validate"""
        assert_true(
            fields.URLField.validate('https://www.example.com/file.pdf')
        )
        assert_false(fields.URLField.validate('example.limo'))

    def test_bool_field_validate(self):
        """Test boolean field validate"""
        assert_true(fields.BoolField.validate('0'))
        assert_true(fields.BoolField.validate('1'))
        assert_true(fields.BoolField.validate('True'))
        assert_true(fields.BoolField.validate('false'))
        assert_false(fields.BoolField.validate('anything else'))

    def test_color_field_validate(self):
        """Test color field validate"""
        assert_true(fields.ColorField.validate('#f09'))
        assert_true(fields.ColorField.validate('#123ABC'))
        assert_false(fields.ColorField.validate('#1234'))
        assert_false(fields.ColorField.validate('#1234gh'))
        assert_false(fields.ColorField.validate('face12'))

    def test_choice_field_validate_all(self):
        """Test choice field validate"""
        # make random values deterministic
        random.seed(42)
        good = [
            random.randint(1, fields.ChoiceField.max_choices - 1)
            for _ in xrange(20)
        ]
        assert_true(fields.ChoiceField.validate_all(good))

        bad = [
            random.randint(0, 10 * fields.ChoiceField.max_choices)
            for _ in xrange(20)
        ]
        assert_false(fields.ChoiceField.validate_all(bad))

    def test_date_field_validate(self):
        """Test date field validate"""
        assert_true(fields.DateField.validate('2017-01-13'))
        assert_true(fields.DateField.validate('Jan 1, 17'))
        assert_true(fields.DateField.validate('February 20, 1999'))
        assert_true(fields.DateField.validate('12/31/12'))
        assert_false(fields.DateField.validate('2017-01-33'))
        assert_false(fields.DateField.validate('Foo 1, 17'))
        assert_false(fields.DateField.validate('February 20, 199'))
        assert_false(fields.DateField.validate('The first of may'))


class TestDataSetViews(TestCase):
    """Test the data set views"""

    def setUp(self):
        self.request_factory = RequestFactory()
        self.user = UserFactory()
        csv = StringIO(
            'name,age,job\n'
            'alice,24,engineer\n'
            'bob,45,journalist\n'
            'charlie,62,doctor\n'
        )
        self.dataset = DataSet.objects.create_from_csv(
            'DataSet',
            self.user,
            csv,
        )

    def test_detail(self):
        """Test the detail view"""
        request = self.request_factory.get(
            reverse(
                'dataset-detail',
                kwargs={
                    'slug': self.dataset.slug,
                    'idx': self.dataset.pk
                }
            )
        )
        request = mock_middleware(request)
        request.user = self.user
        response = views.detail(
            request,
            self.dataset.slug,
            self.dataset.pk,
        )
        eq_(response.status_code, 200)

    def test_embed(self):
        """Test the embed view"""
        request = self.request_factory.get(
            reverse(
                'dataset-embed',
                kwargs={
                    'slug': self.dataset.slug,
                    'idx': self.dataset.pk
                }
            )
        )
        request = mock_middleware(request)
        request.user = self.user
        response = views.embed(
            request,
            self.dataset.slug,
            self.dataset.pk,
        )
        eq_(response.status_code, 200)

    def test_data(self):
        """Test the data view"""
        request = self.request_factory.get(
            reverse(
                'dataset-data',
                kwargs={
                    'slug': self.dataset.slug,
                    'idx': self.dataset.pk
                }
            )
        )
        request = mock_middleware(request)
        request.user = self.user
        response = views.data(
            request,
            self.dataset.slug,
            self.dataset.pk,
        )
        eq_(response.status_code, 200)

    def test_parse_params(self):
        """Test the tabulator parameter parsing function"""
        # pylint: disable=protected-access
        params = {
            'filters[0][field]': 'a',
            'filters[0][type]': '=',
            'filters[0][value]': 'foo',
            'filters[1][field]': 'b',
            'filters[1][type]': 'like',
            'filters[1][value]': 'bar',
        }
        data = views._parse_params(
            params,
            'filters',
            ('field', 'type', 'value'),
        )
        eq_(
            data,
            [
                {
                    'field': 'a',
                    'type': '=',
                    'value': 'foo',
                },
                {
                    'field': 'b',
                    'type': 'like',
                    'value': 'bar',
                },
            ],
        )

        # bad data causes it to return an empty list
        # missing value
        params = {
            'filters[0][field]': 'a',
            'filters[0][type]': '=',
            'filters[0][value]': 'foo',
            'filters[1][field]': 'b',
            'filters[1][type]': 'like',
        }
        data = views._parse_params(
            params,
            'filters',
            ('field', 'type', 'value'),
        )
        eq_(data, [])

        # bad format
        params = {
            'filters[0][field]': 'a',
            'filters[0][type]': '=',
            'filters[0][value]': 'foo',
            'filters[1][field]': 'b',
            'filters[1][type]': 'like',
            'filters[1]{value}': 'bar',
        }
        data = views._parse_params(
            params,
            'filters',
            ('field', 'type', 'value'),
        )
        eq_(data, [])

        # bad field
        params = {
            'filters[0][field]': 'a',
            'filters[0][type]': '=',
            'filters[0][value]': 'foo',
            'filters[1][field]': 'b',
            'filters[1][type]': 'like',
            'filters[1][foobar]': 'bar',
        }
        data = views._parse_params(
            params,
            'filters',
            ('field', 'type', 'value'),
        )
        eq_(data, [])
