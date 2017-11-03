# -*- coding: utf-8 -*-
"""
Models for the data set application
"""

from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.fields.jsonb import KeyTransform
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.expressions import RawSQL, OrderBy
from django.template.defaultfilters import slugify

from itertools import izip_longest
import unicodecsv as csv
import xlrd

from muckrock.dataset.fields import FIELDS, FIELD_DICT


class DataSetQuerySet(models.QuerySet):
    """Customer manager for DataSets"""

    def create_from_csv(self, name, user, file_):
        """Create a data set from a csv file"""
        csv_reader = csv.reader(file_)
        dataset = self.create(
                name=name,
                user=user,
                )
        headers = next(csv_reader)
        for i, name in enumerate(headers):
            dataset.fields.create(
                    name=name,
                    field_number=i,
                    )
        slug_headers = [slugify(h) for h in headers]
        headers_len = len(headers)
        for i, row in enumerate(csv_reader):
            dataset.rows.create(
                    data=dict(izip_longest(
                        slug_headers,
                        row[:headers_len],
                        fillvalue='',
                        )),
                    row_number=i,
                    )

        dataset.detect_field_types()
        return dataset

    def create_from_xls(self, name, user, file_):
        """Create a data set from an xls file"""
        book = xlrd.open_workbook(file_contents=file_.read())
        sheet = book.sheet_by_index(0)

        dataset = self.create(
                name=name,
                user=user,
                )

        headers = sheet.row_values(0)
        for i, name in enumerate(headers):
            dataset.fields.create(
                    name=name,
                    field_number=i,
                    )
        slug_headers = [slugify(h) for h in headers]
        for i in xrange(1, sheet.nrows):
            row = [unicode(v) for v in sheet.row_values(i)]
            dataset.rows.create(
                    data=dict(zip(slug_headers, row)),
                    row_number=i,
                    )

        dataset.detect_field_types()
        return dataset


class DataSet(models.Model):
    """A set of data"""
    name = models.CharField(
            max_length=255,
            )
    slug = models.SlugField(
            max_length=255,
            )
    user = models.ForeignKey(
            'auth.User',
            on_delete=models.PROTECT,
            )
    created_datetime = models.DateTimeField(auto_now_add=True)
    custom_format = models.CharField(
            max_length=5,
            choices=(('', '---'), ('email', 'Email Viewer')),
            blank=True,
            )

    objects = DataSetQuerySet.as_manager()

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        """The url for this object"""
        return reverse(
                'dataset-detail',
                kwargs={'slug': self.slug, 'idx': self.pk},
                )

    def detect_field_types(self):
        """Auto detect column types"""
        # only look at first 100 rows, as there could be a lot of data
        rows = self.rows.all()[:100]
        fields = self.fields.all()
        for field in fields:
            for field_type in FIELDS:
                has_validate_all = hasattr(field_type, 'validate_all')
                validate_all = (has_validate_all and
                        field_type.validate_all(
                            [row.data[field.slug] for row in rows]))
                all_valid = (not has_validate_all and
                        all(field_type.validate(row.data[field.slug])
                        for row in rows))
                if validate_all or all_valid:
                    field.type = field_type.slug
                    field.save()
                    break

    def save(self, *args, **kwargs):
        """Save the slug"""
        self.slug = slugify(self.name)
        super(DataSet, self).save(*args, **kwargs)


FIELD_CHOICES = [(f.slug, f.name) for f in FIELDS]


class DataField(models.Model):
    """A column of a data set"""
    dataset = models.ForeignKey(
            DataSet,
            related_name='fields',
            on_delete=models.CASCADE,
            )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    field_number = models.PositiveSmallIntegerField()
    type = models.CharField(
            max_length=6,
            choices=FIELD_CHOICES,
            default='text',
            )

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Save the slug"""
        self.slug = slugify(self.name)
        super(DataField, self).save(*args, **kwargs)

    def formatter(self):
        """The tabulator formatter for this field"""
        return self.field.formatter

    def editor(self):
        """The tabulator editor for this field"""
        return self.field.editor

    def choices(self):
        """Get all possible values for a choices field type"""
        return (self.dataset.rows
                .annotate(choices=KeyTransform(self.slug, 'data'))
                .values_list('choices', flat=True)
                .order_by()
                .distinct()
                )

    @property
    def field(self):
        """Get the field object for this field type"""
        return FIELD_DICT[self.type]

    class Meta:
        ordering = ('field_number',)
        unique_together = [
                ('dataset', 'name'),
                ('dataset', 'slug'),
                ('dataset', 'field_number'),
                ]


FILTER_TYPES = {
        'like': 'icontains',
        '=': 'iexact',
        '<': 'lt',
        '<=': 'lte',
        '>': 'gt',
        '>=': 'gte',
        'ne': 'iexact',
        }


class DataRowQuerySet(models.QuerySet):
    """Customer manager for DataSets"""

    def sort(self, fields, sorters):
        """Sort the data given tabulator style sorter params"""
        queryset = self.all()
        for sorter in sorters:
            if sorter['field'] not in fields:
                continue
            descending = sorter['dir'] == 'desc'
            type_ = fields[sorter['field']].field.sort_type
            queryset = queryset.order_by(
                    OrderBy(
                        RawSQL('(data->>%s)::{}'.format(type_), (sorter['field'],)),
                        descending=descending,
                        ))
        return queryset

    def tabulator_filter(self, fields, filters):
        """Filter data given tabulator style filter params"""
        queryset = self.all()
        for filter_ in filters:
            if filter_['field'] not in fields:
                continue
            kwargs = {
                    'data__{}__{}'.format(filter_['field'], FILTER_TYPES[filter_['type']]):
                    filter_['value']
                    }
            if filter_['type'] == '!=':
                queryset = queryset.exclude(**kwargs)
            else:
                queryset = queryset.filter(**kwargs)
        return queryset


class DataRow(models.Model):
    """A row of a data set"""
    dataset = models.ForeignKey(
            DataSet,
            related_name='rows',
            on_delete=models.CASCADE,
            )
    row_number = models.PositiveIntegerField(db_index=True)
    data = JSONField()

    objects = DataRowQuerySet.as_manager()

    def __unicode__(self):
        return u'Row #{}'.format(self.row_number)

    class Meta:
        ordering = ('row_number',)
        unique_together = ('dataset', 'row_number')
