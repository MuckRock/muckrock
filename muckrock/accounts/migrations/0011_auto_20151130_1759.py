# -*- coding: utf-8 -*-

# Django
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_merge'),
    ]

    operations = [
        migrations.RenameField(
            model_name='statistics',
            old_name='daily_requests_community',
            new_name='daily_requests_basic',
        ),
        migrations.AlterField(
            model_name='profile',
            name='acct_type',
            field=models.CharField(
                max_length=10,
                choices=[('admin', 'Admin'), ('basic', 'Basic'),
                         ('beta', 'Beta'), ('pro', 'Professional'),
                         ('proxy', 'Proxy'), ('robot', 'Robot')]
            ),
        ),
    ]
