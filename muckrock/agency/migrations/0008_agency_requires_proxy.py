# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0007_agency_location'),
    ]

    operations = [
        migrations.AddField(
            model_name='agency',
            name='requires_proxy',
            field=models.BooleanField(default=False),
        ),
    ]
