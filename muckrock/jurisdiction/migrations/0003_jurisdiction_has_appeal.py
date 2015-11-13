# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jurisdiction', '0002_auto_20150618_2306'),
    ]

    operations = [
        migrations.AddField(
            model_name='jurisdiction',
            name='has_appeal',
            field=models.BooleanField(default=True, help_text=b'Does this jurisdiction have an appeals process?'),
        ),
    ]
