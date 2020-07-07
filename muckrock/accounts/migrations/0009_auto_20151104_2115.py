# -*- coding: utf-8 -*-

# Django
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_statistics_requests_processing_days'),
    ]

    operations = [
        migrations.AddField(
            model_name='statistics',
            name='daily_robot_response_tasks',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='acct_type',
            field=models.CharField(
                max_length=10,
                choices=[('admin', 'Admin'), ('beta', 'Beta'),
                         ('community', 'Community'), ('pro', 'Professional'),
                         ('proxy', 'Proxy'), ('robot', 'Robot')]
            ),
        ),
    ]
