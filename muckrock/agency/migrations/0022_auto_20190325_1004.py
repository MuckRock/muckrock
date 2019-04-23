# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2019-03-25 14:04
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0021_remove_agency_location'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='agency',
            options={'permissions': (('view_emails', 'Can view private contact information'), ('merge_agency', 'Can merge two agencies together')), 'verbose_name_plural': 'agencies'},
        ),
        migrations.AlterField(
            model_name='agency',
            name='appeal_agency',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='appeal_for', to='agency.Agency'),
        ),
    ]