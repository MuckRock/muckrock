# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crowdfund', '0003_auto_20150618_2306'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='crowdfundproject',
            name='payments',
        ),
        migrations.RemoveField(
            model_name='crowdfundproject',
            name='project',
        ),
        migrations.RemoveField(
            model_name='crowdfundprojectpayment',
            name='crowdfund',
        ),
        migrations.RemoveField(
            model_name='crowdfundprojectpayment',
            name='user',
        ),
        migrations.RemoveField(
            model_name='project',
            name='foias',
        ),
        migrations.DeleteModel(
            name='CrowdfundProject',
        ),
        migrations.DeleteModel(
            name='CrowdfundProjectPayment',
        ),
        migrations.DeleteModel(
            name='Project',
        ),
    ]
