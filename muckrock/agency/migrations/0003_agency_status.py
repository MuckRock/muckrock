# -*- coding: utf-8 -*-

# Django
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0002_auto_20150618_2306'),
    ]

    operations = [
        migrations.AddField(
            model_name='agency',
            name='status',
            field=models.CharField(
                default='pending',
                max_length=8,
                choices=[('pending', 'Pending'), ('approved', 'Approved'),
                         ('rejected', 'Rejected')]
            ),
        ),
    ]
