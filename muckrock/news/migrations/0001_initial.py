# -*- coding: utf-8 -*-

# Django
from django.conf import settings
from django.db import migrations, models
from django.utils import timezone

# Standard Library
import datetime

# Third Party
import easy_thumbnails.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('foia', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
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
                (
                    'pub_date',
                    models.DateTimeField(
                        default=timezone.now, verbose_name='Publish date'
                    )
                ),
                ('title', models.CharField(max_length=200)),
                ('kicker', models.CharField(max_length=200, blank=True)),
                (
                    'slug',
                    models.SlugField(
                        help_text=
                        'A "Slug" is a unique URL-friendly title for an object.',
                        unique=True
                    )
                ),
                (
                    'summary',
                    models.TextField(
                        help_text=
                        'A single paragraph summary or preview of the article.'
                    )
                ),
                ('body', models.TextField(verbose_name='Body text')),
                (
                    'publish',
                    models.BooleanField(
                        default=False,
                        help_text=
                        'Articles do not appear on the site until their publish date.',
                        verbose_name='Publish on site'
                    )
                ),
                (
                    'image',
                    easy_thumbnails.fields.ThumbnailerImageField(
                        null=True, upload_to='news_images', blank=True
                    )
                ),
                (
                    'authors',
                    models.ManyToManyField(
                        related_name='authored_articles',
                        to=settings.AUTH_USER_MODEL
                    )
                ),
                (
                    'editors',
                    models.ManyToManyField(
                        related_name='edited_articles',
                        null=True,
                        to=settings.AUTH_USER_MODEL,
                        blank=True
                    )
                ),
                (
                    'foias',
                    models.ManyToManyField(
                        related_name='articles',
                        null=True,
                        to='foia.FOIARequest',
                        blank=True
                    )
                ),
            ],
            options={
                'ordering': ['-pub_date'],
                'get_latest_by': 'pub_date',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Photo',
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
                ('image', models.ImageField(upload_to='news_photos')),
            ],
            options={},
            bases=(models.Model,),
        ),
    ]
