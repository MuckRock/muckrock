# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0011_auto_20160228_1056'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='NewCrowdfundTask',
            new_name='CrowdfundTask',
        ),
    ]
