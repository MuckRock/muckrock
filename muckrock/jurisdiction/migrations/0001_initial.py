# -*- coding: utf-8 -*-

# Django
from django.db import migrations, models

# Third Party
import easy_thumbnails.fields

# MuckRock
import muckrock.jurisdiction.models


class Migration(migrations.Migration):

    dependencies = [
        ('business_days', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Jurisdiction',
            fields=[
                (
                    'id',
                    models.AutoField(
                        verbose_name='ID',
                        serialize=False,
                        auto_created=True,
                        primary_key=True
                    )
                ),
                ('name', models.CharField(max_length=50)),
                ('slug', models.SlugField(max_length=55)),
                ('full_name', models.CharField(max_length=55, blank=True)),
                ('abbrev', models.CharField(max_length=5, blank=True)),
                (
                    'level',
                    models.CharField(
                        max_length=1,
                        choices=[('f', 'Federal'), ('s', 'State'),
                                 ('l', 'Local')]
                    )
                ),
                ('hidden', models.BooleanField(default=False)),
                (
                    'image',
                    easy_thumbnails.fields.ThumbnailerImageField(
                        null=True, upload_to='jurisdiction_images', blank=True
                    )
                ),
                (
                    'image_attr_line',
                    models.CharField(
                        help_text='May use html', max_length=255, blank=True
                    )
                ),
                (
                    'public_notes',
                    models.TextField(help_text='May use html', blank=True)
                ),
                (
                    'days',
                    models.PositiveSmallIntegerField(
                        help_text='How many days do they have to respond?',
                        null=True,
                        blank=True
                    )
                ),
                (
                    'observe_sat',
                    models.BooleanField(
                        help_text=
                        'Are holidays observed on Saturdays? (or are they moved to Friday?)'
                    )
                ),
                (
                    'use_business_days',
                    models.BooleanField(
                        default=True,
                        help_text=
                        'Response time in business days (or calendar days)?'
                    )
                ),
                (
                    'intro',
                    models.TextField(
                        help_text=
                        'Intro paragraph for request - usually includes the pertinant FOI law',
                        blank=True
                    )
                ),
                (
                    'law_name',
                    models.CharField(
                        help_text='The pertinant FOIA law',
                        max_length=255,
                        blank=True
                    )
                ),
                (
                    'waiver',
                    models.TextField(
                        help_text=
                        'Optional - custom waiver paragraph if FOI law has special line for waivers',
                        blank=True
                    )
                ),
                (
                    'holidays',
                    models.ManyToManyField(
                        to='business_days.Holiday', blank=True
                    )
                ),
                (
                    'parent',
                    models.ForeignKey(
                        related_name='children',
                        blank=True,
                        to='jurisdiction.Jurisdiction',
                        null=True
                    )
                ),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model, muckrock.jurisdiction.models.RequestHelper),
        ),
        migrations.AlterUniqueTogether(
            name='jurisdiction',
            unique_together=set([('slug', 'parent')]),
        ),
    ]
