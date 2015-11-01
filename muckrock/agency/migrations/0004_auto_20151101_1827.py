# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def set_agency_status(apps, schema_editor):
    """Set the status field based on the approved field
    and if an open NewAgencyTask exists or not"""
    Agency = apps.get('agency', 'Agency')
    NewAgencyTask = apps.get('task', 'NewAgencyTask')
    # if it is approved, its status is approved
    for agency in Agency.objects.filter(approved=True):
        agency.status = 'approved'
        agency.save()
    # if it is not approved, mark it as rejected
    for agency in Agency.objects.filter(approved=False):
        agency.status = 'rejected'
        agency.save()
    # if it has an unresolved NewAgencyTask, it is pending
    for task in NewAgencyTask.objects.filter(resolved=False):
        task.agency.status = 'pending'
        task.agency.save()

class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0003_agency_status'),
        ('task', '0005_auto_20151007_2148'),
    ]

    operations = [
        migrations.RunPython(set_agency_status),
    ]
