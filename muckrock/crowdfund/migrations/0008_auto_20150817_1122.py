# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crowdfund', '0007_crowdfundprojectpayment'),
    ]

    operations = [
        migrations.AddField(
            model_name='crowdfundproject',
            name='payment_capped',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='crowdfundrequest',
            name='payment_capped',
            field=models.BooleanField(default=False),
        ),
    ]
