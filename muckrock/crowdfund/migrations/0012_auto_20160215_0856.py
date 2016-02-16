# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crowdfund', '0011_auto_20160127_1834'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='crowdfund',
            name='foia',
        ),
        migrations.RemoveField(
            model_name='crowdfund',
            name='project',
        ),
    ]
