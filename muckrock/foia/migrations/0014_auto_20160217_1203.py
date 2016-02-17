# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foia', '0013_auto_20151215_2035'),
    ]

    operations = [
        migrations.AlterField(
            model_name='foianote',
            name='datetime',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
