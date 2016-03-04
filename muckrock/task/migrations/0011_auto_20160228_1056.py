# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0010_merge'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='crowdfundtask',
            name='crowdfund',
        ),
        migrations.RemoveField(
            model_name='crowdfundtask',
            name='task_ptr',
        ),
        migrations.RemoveField(
            model_name='genericcrowdfundtask',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='genericcrowdfundtask',
            name='task_ptr',
        ),
        migrations.DeleteModel(
            name='CrowdfundTask',
        ),
        migrations.DeleteModel(
            name='GenericCrowdfundTask',
        ),
    ]
