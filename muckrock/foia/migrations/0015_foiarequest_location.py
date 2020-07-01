# -*- coding: utf-8 -*-


# Django
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foia', '0014_auto_20160217_1203'),
    ]

    operations = [
        migrations.AddField(
            model_name='foiarequest',
            name='location',
            #field=djgeojson.fields.PointField(blank=True),
            # changing so I can uninstall djgeojson, this field is later removed
            field=models.CharField(max_length=1),
        ),
    ]
