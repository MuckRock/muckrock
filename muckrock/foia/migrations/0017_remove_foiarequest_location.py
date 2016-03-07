# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foia', '0016_merge'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='foiarequest',
            name='location',
        ),
    ]
