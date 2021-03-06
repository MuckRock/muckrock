# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-02-06 15:04


# Django
from django.db import migrations


def copy_tracking_id(apps, schema_editor):
    FOIARequest = apps.get_model('foia', 'FOIARequest')
    TrackingNumber = apps.get_model('foia', 'TrackingNumber')
    for foia in FOIARequest.objects.exclude(tracking_id=''):
        foia.tracking_ids.create(
            tracking_id=foia.tracking_id,
            reason='initial',
        )


def delete_tracking_ids(apps, schema_editor):
    TrackingNumber = apps.get_model('foia', 'TrackingNumber')
    TrackingNumber.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('foia', '0044_auto_20180206_1557'),
    ]

    operations = [migrations.RunPython(copy_tracking_id, delete_tracking_ids)]
