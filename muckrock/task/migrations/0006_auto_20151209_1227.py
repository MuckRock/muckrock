# -*- coding: utf-8 -*-


# Django
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0005_auto_20151007_2148'),
    ]

    operations = [
        migrations.AlterField(
            model_name='flaggedtask',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
