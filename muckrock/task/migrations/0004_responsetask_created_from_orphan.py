# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0003_genericcrowdfundtask'),
    ]

    operations = [
        migrations.AddField(
            model_name='responsetask',
            name='created_from_orphan',
            field=models.BooleanField(default=False),
        ),
    ]
