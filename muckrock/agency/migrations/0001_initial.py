# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import muckrock.core.fields
import easy_thumbnails.fields
from django.conf import settings
import muckrock.jurisdiction.models


class Migration(migrations.Migration):

    dependencies = [
        ('jurisdiction', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Agency',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(max_length=255)),
                ('approved', models.BooleanField()),
                ('can_email_appeals', models.BooleanField()),
                ('image', easy_thumbnails.fields.ThumbnailerImageField(null=True, upload_to=b'agency_images', blank=True)),
                ('image_attr_line', models.CharField(help_text=b'May use html', max_length=255, blank=True)),
                ('public_notes', models.TextField(help_text=b'May use html', blank=True)),
                ('stale', models.BooleanField(default=False)),
                ('address', models.TextField(blank=True)),
                ('email', models.EmailField(max_length=75, blank=True)),
                ('other_emails', muckrock.core.fields.EmailsListField(max_length=255, blank=True)),
                ('contact_salutation', models.CharField(max_length=30, blank=True)),
                ('contact_first_name', models.CharField(max_length=100, blank=True)),
                ('contact_last_name', models.CharField(max_length=100, blank=True)),
                ('contact_title', models.CharField(max_length=255, blank=True)),
                ('url', models.URLField(help_text=b'Begin with http://', verbose_name=b'FOIA Web Page', blank=True)),
                ('expires', models.DateField(null=True, blank=True)),
                ('phone', models.CharField(max_length=30, blank=True)),
                ('fax', models.CharField(max_length=30, blank=True)),
                ('notes', models.TextField(blank=True)),
                ('aliases', models.TextField(blank=True)),
                ('website', models.CharField(max_length=255, blank=True)),
                ('twitter', models.CharField(max_length=255, blank=True)),
                ('twitter_handles', models.TextField(blank=True)),
                ('foia_logs', models.URLField(help_text=b'Begin with http://', verbose_name=b'FOIA Logs', blank=True)),
                ('foia_guide', models.URLField(help_text=b'Begin with http://', verbose_name=b'FOIA Processing Guide', blank=True)),
                ('exempt', models.BooleanField(default=False)),
                ('appeal_agency', models.ForeignKey(blank=True, to='agency.Agency', null=True)),
                ('jurisdiction', models.ForeignKey(related_name='agencies', to='jurisdiction.Jurisdiction')),
                ('parent', models.ForeignKey(related_name='children', blank=True, to='agency.Agency', null=True)),
            ],
            options={
                'verbose_name_plural': 'agencies',
            },
            bases=(models.Model, muckrock.jurisdiction.models.RequestHelper),
        ),
        migrations.CreateModel(
            name='AgencyType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=60)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='agency',
            name='types',
            field=models.ManyToManyField(to='agency.AgencyType', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='agency',
            name='user',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
    ]
