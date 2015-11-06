# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_remove_profile_follow_questions'),
    ]

    operations = [
        migrations.AddField(
            model_name='statistics',
            name='requests_processing_days',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
