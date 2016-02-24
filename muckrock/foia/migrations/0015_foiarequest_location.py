# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import djgeojson.fields


class Migration(migrations.Migration):

    dependencies = [
        ('foia', '0014_auto_20160217_1203'),
    ]

    operations = [
        migrations.AddField(
            model_name='foiarequest',
            name='location',
            field=djgeojson.fields.PointField(blank=True),
        ),
    ]
