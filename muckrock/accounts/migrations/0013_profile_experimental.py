# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_profile_payment_failed'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='experimental',
            field=models.BooleanField(default=False),
        ),
    ]
