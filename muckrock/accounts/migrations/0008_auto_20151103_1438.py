# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_remove_profile_follow_questions'),
    ]

    operations = [
        migrations.RenameField(
            model_name='profile',
            old_name='stripe_id',
            new_name='customer_id',
        ),
        migrations.AddField(
            model_name='profile',
            name='subscription_id',
            field=models.CharField(max_length=255, blank=True),
        ),
    ]
