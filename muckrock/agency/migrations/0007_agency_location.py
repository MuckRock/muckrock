# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import djgeojson.fields


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0006_agency_payable_to'),
    ]

    operations = [
        migrations.AddField(
            model_name='agency',
            name='location',
            field=djgeojson.fields.PointField(blank=True),
        ),
    ]
