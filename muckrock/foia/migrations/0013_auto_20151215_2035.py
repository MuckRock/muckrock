# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def set_date_updated(apps, schema_editor):
    """Initialize the date_updated field"""
    FOIARequest = apps.get_model('foia', 'FOIARequest')
    for foia in FOIARequest.objects.all():
        last_comm = foia.communications.last()
        if last_comm:
            foia.date_updated = foia.communications.last().date
            foia.save()


class Migration(migrations.Migration):

    dependencies = [
        ('foia', '0012_foiarequest_date_updated'),
    ]

    operations = [
        migrations.RunPython(set_date_updated),
    ]
