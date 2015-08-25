# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_auto_20150618_2306'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='follows_foia',
        ),
    ]
