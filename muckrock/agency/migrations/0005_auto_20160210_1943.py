# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0004_auto_20151101_1827'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='agency',
            name='approved',
        ),
        migrations.RemoveField(
            model_name='agency',
            name='expires',
        ),
    ]
