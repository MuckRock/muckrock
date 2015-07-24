# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('foia', '0003_auto_20150618_2306'),
    ]

    operations = [
        migrations.AlterField(
            model_name='foiarequest',
            name='price',
            field=models.DecimalField(default=b'0.00', max_digits=14, decimal_places=2),
        ),
    ]
