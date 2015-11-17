# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0002_auto_20150715_1413'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='date_update',
            field=models.DateField(auto_now_add=True, null=True),
        ),
        migrations.AlterField(
            model_name='organization',
            name='max_users',
            field=models.IntegerField(default=3),
        ),
        migrations.AlterField(
            model_name='organization',
            name='monthly_cost',
            field=models.IntegerField(default=10000),
        ),
        migrations.AlterField(
            model_name='organization',
            name='monthly_requests',
            field=models.IntegerField(default=50),
        ),
    ]
