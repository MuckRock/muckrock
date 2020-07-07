# -*- coding: utf-8 -*-

# Django
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foia', '0003_auto_20150618_2306'),
    ]

    operations = [
        migrations.AlterField(
            model_name='foiarequest',
            name='price',
            field=models.DecimalField(
                default='0.00', max_digits=14, decimal_places=2
            ),
        ),
    ]
