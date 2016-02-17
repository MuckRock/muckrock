# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0008_auto_20160216_1500'),
    ]

    operations = [
        migrations.AlterField(
            model_name='snailmailtask',
            name='amount',
            field=models.DecimalField(default=0.0, max_digits=8, decimal_places=2),
        ),
    ]
