# -*- coding: utf-8 -*-

# Django
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sidebar', '0002_auto_20150717_1142'),
    ]

    operations = [
        migrations.AlterField(
            model_name='broadcast',
            name='context',
            field=models.CharField(
                unique=True,
                max_length=255,
                choices=[('admin', 'Admin'), ('beta', 'Beta'),
                         ('community', 'Community'), ('pro', 'Professional'),
                         ('proxy',
                          'Proxy'), ('robot',
                                     'Robot'), ('anonymous', 'Visitor')]
            ),
        ),
    ]
