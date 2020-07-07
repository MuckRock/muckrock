# -*- coding: utf-8 -*-

# Django
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0002_project_summary'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='featured',
            field=models.BooleanField(
                default=False,
                help_text='Featured projects will appear on the homepage.'
            ),
        ),
    ]
