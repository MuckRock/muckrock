# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('foia', '0006_foiarequest_access_key'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='foianote',
            options={'ordering': ['foia', 'datetime'], 'verbose_name': 'FOIA Note'},
        ),
        migrations.RenameField(
            model_name='foianote',
            old_name='date',
            new_name='datetime',
        ),
        migrations.AddField(
            model_name='foianote',
            name='author',
            field=models.ForeignKey(related_name='notes', to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
