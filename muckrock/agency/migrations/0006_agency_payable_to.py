# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0005_auto_20160210_1943'),
    ]

    operations = [
        migrations.AddField(
            model_name='agency',
            name='payable_to',
            field=models.ForeignKey(related_name='receivable', blank=True, to='agency.Agency', null=True),
        ),
    ]
