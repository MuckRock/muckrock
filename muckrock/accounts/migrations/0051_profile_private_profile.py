# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2020-02-19 14:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0050_auto_20190307_1406'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='private_profile',
            field=models.BooleanField(default=False, help_text=b'Keep your profile private even if you have filed requests'),
        ),
    ]