# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jurisdiction', '0003_jurisdiction_has_appeal'),
    ]

    operations = [
        migrations.AddField(
            model_name='jurisdiction',
            name='requires_proxy',
            field=models.BooleanField(default=False),
        ),
    ]
