# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foia', '0009_foiarequest_date_processing'),
    ]

    operations = [
        migrations.AddField(
            model_name='foiacommunication',
            name='thanks',
            field=models.BooleanField(default=False),
        ),
    ]
