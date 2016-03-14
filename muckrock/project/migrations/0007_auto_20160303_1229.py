# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0006_merge'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='projectmap',
            name='project',
        ),
        migrations.RemoveField(
            model_name='projectmap',
            name='requests',
        ),
        migrations.DeleteModel(
            name='ProjectMap',
        ),
    ]
