# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0002_auto_20150618_2306'),
    ]

    operations = [
        migrations.AddField(
            model_name='agency',
            name='status',
            field=models.CharField(default=b'pending', max_length=8, choices=[(b'pending', b'Pending'), (b'approved', b'Approved'), (b'rejected', b'Rejected')]),
        ),
    ]
