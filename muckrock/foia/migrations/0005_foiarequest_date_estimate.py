# -*- coding: utf-8 -*-

# Django
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foia', '0004_auto_20150719_1138'),
    ]

    operations = [
        migrations.AddField(
            model_name='foiarequest',
            name='date_estimate',
            field=models.DateField(
                null=True, verbose_name='Estimated Date Completed', blank=True
            ),
        ),
    ]
