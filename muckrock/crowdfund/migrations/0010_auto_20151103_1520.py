# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crowdfund', '0009_auto_20150818_1117'),
    ]

    operations = [
        migrations.AddField(
            model_name='crowdfundprojectpayment',
            name='charge_id',
            field=models.CharField(max_length=255, blank=True),
        ),
        migrations.AddField(
            model_name='crowdfundrequestpayment',
            name='charge_id',
            field=models.CharField(max_length=255, blank=True),
        ),
    ]
