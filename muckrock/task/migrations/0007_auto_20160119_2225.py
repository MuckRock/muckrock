# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0006_auto_20151209_1227'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='resolved',
            field=models.BooleanField(default=False, db_index=True),
        ),
    ]
