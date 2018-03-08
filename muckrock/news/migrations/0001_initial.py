# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings
import easy_thumbnails.fields
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('foia', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pub_date', models.DateTimeField(default=timezone.now, verbose_name=b'Publish date')),
                ('title', models.CharField(max_length=200)),
                ('kicker', models.CharField(max_length=200, blank=True)),
                ('slug', models.SlugField(help_text=b'A "Slug" is a unique URL-friendly title for an object.', unique=True)),
                ('summary', models.TextField(help_text=b'A single paragraph summary or preview of the article.')),
                ('body', models.TextField(verbose_name=b'Body text')),
                ('publish', models.BooleanField(default=False, help_text=b'Articles do not appear on the site until their publish date.', verbose_name=b'Publish on site')),
                ('image', easy_thumbnails.fields.ThumbnailerImageField(null=True, upload_to=b'news_images', blank=True)),
                ('authors', models.ManyToManyField(related_name='authored_articles', to=settings.AUTH_USER_MODEL)),
                ('editors', models.ManyToManyField(related_name='edited_articles', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
                ('foias', models.ManyToManyField(related_name='articles', null=True, to='foia.FOIARequest', blank=True)),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('image', models.ImageField(upload_to=b'news_photos')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
