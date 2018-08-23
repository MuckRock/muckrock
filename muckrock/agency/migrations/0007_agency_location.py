# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Django
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0006_agency_payable_to'),
    ]

    operations = [
        migrations.AddField(
            model_name='agency',
            name='location',
            #field=djgeojson.fields.PointField(blank=True),
            # changing so I can uninstall djgeojson, this field is later removed
            field=models.CharField(max_length=1),
        ),
    ]
