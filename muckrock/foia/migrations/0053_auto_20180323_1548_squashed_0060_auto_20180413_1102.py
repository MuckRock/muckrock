# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-04-19 19:11
from __future__ import unicode_literals

# Django
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

# MuckRock
import muckrock.foia.models.attachment


class Migration(migrations.Migration):

    replaces = [
        (b'foia',
         '0055_auto_20180323_1548'), (b'foia', '0056_auto_20180326_1409'),
        (b'foia',
         '0057_auto_20180326_1412'), (b'foia', '0058_auto_20180326_1413'),
        (b'foia',
         '0059_auto_20180327_1157'), (b'foia', '0060_auto_20180413_1102')
    ]

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('foia', '0052_foiamultirequest_composer'),
    ]

    operations = [
        migrations.RenameField(
            model_name='foiarequest',
            old_name='date_done',
            new_name='datetime_done',
        ),
        migrations.RenameField(
            model_name='foiarequest',
            old_name='date_updated',
            new_name='datetime_updated',
        ),
        migrations.CreateModel(
            name='OutboundComposerAttachment',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID'
                    )
                ),
                (
                    'ffile',
                    models.FileField(
                        max_length=255,
                        upload_to=muckrock.foia.models.attachment.
                        attachment_path,
                        verbose_name=b'file'
                    )
                ),
                ('date_time_stamp', models.DateTimeField()),
                ('sent', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterModelOptions(
            name='foiacomposer',
            options={
                'permissions': (('view_foiacomposer', 'Can view this composer'),
                                ),
                'verbose_name':
                    'FOIA Composer'
            },
        ),
        migrations.AlterField(
            model_name='outboundattachment',
            name='ffile',
            field=models.FileField(
                max_length=255,
                upload_to=muckrock.foia.models.attachment.attachment_path,
                verbose_name=b'file'
            ),
        ),
        migrations.AlterField(
            model_name='outboundattachment',
            name='foia',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='pending_request_attachments',
                to='foia.FOIARequest'
            ),
        ),
        migrations.AlterField(
            model_name='outboundattachment',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='pending_outboundattachment',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='outboundcomposerattachment',
            name='composer',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='pending_attachments',
                to='foia.FOIAComposer'
            ),
        ),
        migrations.AddField(
            model_name='outboundcomposerattachment',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='pending_outboundcomposerattachment',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.RenameModel(
            old_name='OutboundAttachment',
            new_name='OutboundRequestAttachment',
        ),
        migrations.AlterField(
            model_name='outboundrequestattachment',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='pending_outboundrequestattachment',
                to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AlterField(
            model_name='outboundrequestattachment',
            name='foia',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='pending_attachments',
                to='foia.FOIARequest'
            ),
        ),
        migrations.AddField(
            model_name='foiacomposer',
            name='delayed_id',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='foiacomposer',
            name='datetime_created',
            field=models.DateTimeField(
                db_index=True, default=django.utils.timezone.now
            ),
        ),
    ]
