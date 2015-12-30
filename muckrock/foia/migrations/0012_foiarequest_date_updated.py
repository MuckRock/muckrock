# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foia', '0011_auto_20151215_2009'),
    ]

    operations = [
        migrations.AddField(
            model_name='foiarequest',
            name='date_updated',
            field=models.DateField(db_index=True, null=True, blank=True),
        ),
    ]
