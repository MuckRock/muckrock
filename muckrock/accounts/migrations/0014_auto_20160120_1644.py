# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def instant_to_hourly(apps, schema_editor):
    """Migrate instant email preference to hourly"""
    Profile = apps.get_model('accounts', 'Profile')
    for profile in Profile.objects.filter(email_pref='instant'):
        profile.email_pref = 'hourly'
        profile.save()

def hourly_to_instant(apps, schema_editor):
    """Migrate hourly email preference to instant"""
    Profile = apps.get_model('accounts', 'Profile')
    for profile in Profile.objects.filter(email_pref='hourly'):
        profile.email_pref = 'instant'
        profile.save()

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_profile_experimental'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='email_pref',
            field=models.CharField(default=b'daily', help_text=b'Receive updates on site activity as an emailed digest.', max_length=10, verbose_name=b'Digest Frequency', choices=[(b'never', b'Never'), (b'hourly', b'Hourly'), (b'daily', b'Daily'), (b'weekly', b'Weekly'), (b'monthly', b'Monthly')]),
        ),
        migrations.RunPython(instant_to_hourly, hourly_to_instant)
    ]
