# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import muckrock.core.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('jurisdiction', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FOIACommunication',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('from_who', models.CharField(max_length=255)),
                ('to_who', models.CharField(max_length=255, blank=True)),
                ('priv_from_who', models.CharField(max_length=255, blank=True)),
                ('priv_to_who', models.CharField(max_length=255, blank=True)),
                ('subject', models.CharField(max_length=255, blank=True)),
                ('date', models.DateTimeField(db_index=True)),
                ('response', models.BooleanField(help_text=b'Is this a response (or a request)?')),
                ('full_html', models.BooleanField(default=False)),
                ('communication', models.TextField(blank=True)),
                ('delivered', models.CharField(blank=True, max_length=10, null=True, choices=[(b'fax', b'Fax'), (b'email', b'Email'), (b'mail', b'Mail')])),
                ('status', models.CharField(blank=True, max_length=10, null=True, choices=[(b'started', b'Draft'), (b'submitted', b'Processing'), (b'ack', b'Awaiting Acknowledgement'), (b'processed', b'Awaiting Response'), (b'appealing', b'Awaiting Appeal'), (b'fix', b'Fix Required'), (b'payment', b'Payment Required'), (b'rejected', b'Rejected'), (b'no_docs', b'No Responsive Documents'), (b'done', b'Completed'), (b'partial', b'Partially Completed'), (b'abandoned', b'Withdrawn')])),
                ('opened', models.BooleanField(default=False, help_text=b'If emailed, did we receive an open notification? If faxed, did we recieve a confirmation?')),
            ],
            options={
                'ordering': ['date'],
                'verbose_name': 'FOIA Communication',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FOIAFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ffile', models.FileField(upload_to=b'foia_files/%Y/%m/%d', max_length=255, verbose_name=b'File')),
                ('title', models.CharField(max_length=255)),
                ('date', models.DateTimeField(null=True, db_index=True)),
                ('source', models.CharField(max_length=255, blank=True)),
                ('description', models.TextField(blank=True)),
                ('access', models.CharField(default=b'public', max_length=12, choices=[(b'public', b'Public'), (b'private', b'Private'), (b'organization', b'Organization')])),
                ('doc_id', models.SlugField(max_length=80, editable=False, blank=True)),
                ('pages', models.PositiveIntegerField(default=0, editable=False)),
            ],
            options={
                'ordering': ['date'],
                'verbose_name': 'FOIA Document File',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FOIAMultiRequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('slug', models.SlugField(max_length=255)),
                ('status', models.CharField(max_length=10, choices=[(b'started', b'Draft'), (b'submitted', b'Processing')])),
                ('embargo', models.BooleanField()),
                ('requested_docs', models.TextField(blank=True)),
            ],
            options={
                'ordering': ['title'],
                'verbose_name': 'FOIA Multi-Request',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FOIANote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField()),
                ('note', models.TextField()),
            ],
            options={
                'ordering': ['foia', 'date'],
                'verbose_name': 'FOIA Note',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FOIARequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('slug', models.SlugField(max_length=255)),
                ('status', models.CharField(max_length=10, choices=[(b'started', b'Draft'), (b'submitted', b'Processing'), (b'ack', b'Awaiting Acknowledgement'), (b'processed', b'Awaiting Response'), (b'appealing', b'Awaiting Appeal'), (b'fix', b'Fix Required'), (b'payment', b'Payment Required'), (b'rejected', b'Rejected'), (b'no_docs', b'No Responsive Documents'), (b'done', b'Completed'), (b'partial', b'Partially Completed'), (b'abandoned', b'Withdrawn')])),
                ('date_submitted', models.DateField(null=True, blank=True)),
                ('date_done', models.DateField(null=True, verbose_name=b'Date response received', blank=True)),
                ('date_due', models.DateField(null=True, blank=True)),
                ('days_until_due', models.IntegerField(null=True, blank=True)),
                ('date_followup', models.DateField(null=True, blank=True)),
                ('embargo', models.BooleanField()),
                ('date_embargo', models.DateField(null=True, blank=True)),
                ('permanent_embargo', models.BooleanField(default=False)),
                ('price', models.DecimalField(default=b'0.00', max_digits=8, decimal_places=2)),
                ('requested_docs', models.TextField(blank=True)),
                ('description', models.TextField(blank=True)),
                ('featured', models.BooleanField()),
                ('tracker', models.BooleanField()),
                ('sidebar_html', models.TextField(blank=True)),
                ('tracking_id', models.CharField(max_length=255, blank=True)),
                ('mail_id', models.CharField(max_length=255, editable=False, blank=True)),
                ('updated', models.BooleanField()),
                ('email', models.EmailField(max_length=75, blank=True)),
                ('other_emails', muckrock.core.fields.EmailsListField(max_length=255, blank=True)),
                ('times_viewed', models.IntegerField(default=0)),
                ('disable_autofollowups', models.BooleanField(default=False)),
                ('block_incoming', models.BooleanField(default=False, help_text=b'Block emails incoming to this request from automatically being posted on the site')),
                ('agency', models.ForeignKey(blank=True, to='agency.Agency', null=True)),
                ('edit_collaborators', models.ManyToManyField(related_name='edit_access', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
                ('jurisdiction', models.ForeignKey(to='jurisdiction.Jurisdiction')),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='foia.FOIARequest', null=True)),
                ('read_collaborators', models.ManyToManyField(related_name='read_access', null=True, to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'ordering': ['title'],
                'verbose_name': 'FOIA Request',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RawEmail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('raw_email', models.TextField(blank=True)),
                ('communication', models.OneToOneField(to='foia.FOIACommunication')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
