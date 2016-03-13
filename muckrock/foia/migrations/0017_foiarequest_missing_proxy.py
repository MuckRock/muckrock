# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foia', '0016_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='foiarequest',
            name='missing_proxy',
            field=models.BooleanField(default=False, help_text=b'This request requires a proxy to file, but no such proxy was avilable up draft creation.'),
        ),
    ]
