# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crowdfund', '0008_auto_20150817_1122'),
    ]

    operations = [
        migrations.AddField(
            model_name='crowdfundproject',
            name='closed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='crowdfundrequest',
            name='closed',
            field=models.BooleanField(default=False),
        ),
    ]
