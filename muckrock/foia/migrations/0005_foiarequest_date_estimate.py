# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('foia', '0004_auto_20150719_1138'),
    ]

    operations = [
        migrations.AddField(
            model_name='foiarequest',
            name='date_estimate',
            field=models.DateField(null=True, verbose_name=b'Estimated Date Completed', blank=True),
        ),
    ]
