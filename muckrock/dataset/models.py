# -*- coding: utf-8 -*-
"""
Models for the data set application
"""

# Django
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.fields.jsonb import KeyTransform
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.expressions import OrderBy, RawSQL
from django.template.defaultfilters import slugify

# Standard Library
import logging
import sys
from collections import defaultdict
from itertools import izip_longest

# MuckRock
from muckrock.dataset.creators import CrowdsourceCreator, CsvCreator, XlsCreator
from muckrock.dataset.fields import FIELD_DICT, FIELDS

logger = logging.getLogger(__name__)


class DataSetQuerySet(models.QuerySet):
    """Customer manager for DataSets"""

    def _unique_slugify(self, headers):
        """Slugify the headers and also make them unique"""
        seen = defaultdict(int)
        slug_headers = []
        for header in headers:
            slug = slugify(header)
            if slug in seen:
                slug_headers.append('{}-{}'.format(slug, seen[slug]))
            else:
                slug_headers.append(slug)
            seen[slug] += 1
        return slug_headers

    def create_from_csv(self, name, user, file_):
        """Create a data set from a csv file"""
        creator = CsvCreator(name, file_)
        return self._create_from(creator, user)

    def create_from_xls(self, name, user, file_):
        """Create a data set from an xls file"""
        creator = XlsCreator(name, file_)
        return self._create_from(creator, user)

    def create_from_crowdsource(self, user, crowdsource):
        """Create a data set from crowdsource's responses"""
        creator = CrowdsourceCreator(crowdsource)
        return self._create_from(creator, user)

    def _create_from(self, creator, user):
        """Create a data set from some source"""
        # pylint: disable=broad-except
        dataset = self.create(
            name=creator.get_name(),
            user=user,
            status='processing',
        )
        try:
            headers = creator.get_headers()
            slug_headers = self._unique_slugify(headers)
            for i, (name, slug) in enumerate(zip(headers, slug_headers)):
                dataset.fields.create(
                    name=name,
                    slug=slug,
                    field_number=i,
                )
            for i, row in enumerate(creator.get_rows()):
                dataset.rows.create(
                    data=dict(izip_longest(
                        slug_headers,
                        row,
                        fillvalue='',
                    )),
                    row_number=i,
                )

            dataset.detect_field_types()
        except Exception as exc:
            logger.error(
                'DataSet creation: %s',
                exc,
                exc_info=sys.exc_info(),
            )
            dataset.status = 'error'
            dataset.save()
        else:
            dataset.status = 'ready'
            dataset.save()
        return dataset


class DataSet(models.Model):
    """A set of data"""
    name = models.CharField(max_length=255,)
    slug = models.SlugField(max_length=255,)
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
    status = models.CharField(
        max_length=10,
        choices=(
            ('processing', 'Processing'),
            ('error', 'Error'),
            ('ready', 'Ready'),
        ),
        default='ready',
    )

    objects = DataSetQuerySet.as_manager()

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        """The url for this object"""
        return reverse(
            'dataset-detail',
            kwargs={'slug': self.slug,
                    'idx': self.pk},
        )

    def detect_field_types(self):
        """Auto detect column types"""
        # only look at first 100 rows, as there could be a lot of data
        rows = self.rows.all()[:100]
        fields = self.fields.all()
        for field in fields:
            for field_type in FIELDS:
                has_validate_all = hasattr(field_type, 'validate_all')
                validate_all = (
                    has_validate_all and field_type.validate_all([
                        row.data[field.slug] for row in rows
                    ])
                )
                all_valid = (
                    not has_validate_all and all(
                        field_type.validate(row.data[field.slug])
                        for row in rows
                    )
                )
                if validate_all or all_valid:
                    field.type = field_type.slug
                    field.save()
                    break

    def save(self, *args, **kwargs):
        """Save the slug"""
        self.slug = slugify(self.name)
        super(DataSet, self).save(*args, **kwargs)


FIELD_CHOICES = [(f.slug, f.name) for f in FIELDS]


class DataFieldQuerySet(models.QuerySet):
    """Customer manager for DataFields"""

    def visible(self):
        """Return all visible fields"""
        return self.filter(hidden=False)


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
    hidden = models.BooleanField(default=False)

    objects = DataFieldQuerySet.as_manager()

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Save the slug"""
        if not self.slug:
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
        return (
            self.dataset.rows.annotate(choices=KeyTransform(self.slug, 'data')
                                       ).values_list('choices', flat=True
                                                     ).order_by().distinct()
        )

    @property
    def field(self):
        """Get the field object for this field type"""
        return FIELD_DICT[self.type]

    class Meta:
        ordering = ('field_number',)
        unique_together = [
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
    '!=': 'iexact',
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
                )
            )
        return queryset

    def tabulator_filter(self, fields, filters):
        """Filter data given tabulator style filter params"""
        queryset = self.all()
        for filter_ in filters:
            if filter_['field'] not in fields:
                continue
            kwargs = {
                'data__{}__{}'.format(
                    filter_['field'], FILTER_TYPES[filter_['type']]
                ):
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
