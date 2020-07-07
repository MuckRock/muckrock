# -*- coding: utf-8 -*-

# Django
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
            field=models.CharField(
                default='daily',
                help_text=
                'Receive updates on site activity as an emailed digest.',
                max_length=10,
                verbose_name='Digest Frequency',
                choices=[('never', 'Never'), ('hourly', 'Hourly'),
                         ('daily', 'Daily'), ('weekly',
                                              'Weekly'), ('monthly', 'Monthly')]
            ),
        ),
        migrations.RunPython(instant_to_hourly, hourly_to_instant)
    ]
