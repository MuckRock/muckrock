# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('foia', '0002_auto_20150614_2154'),
    ]

    operations = [
        migrations.AlterField(
            model_name='foiacommunication',
            name='response',
            field=models.BooleanField(default=False, help_text=b'Is this a response (or a request)?'),
        ),
        migrations.AlterField(
            model_name='foiamultirequest',
            name='agencies',
            field=models.ManyToManyField(related_name='agencies', to='agency.Agency', blank=True),
        ),
        migrations.AlterField(
            model_name='foiamultirequest',
            name='embargo',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='foiarequest',
            name='edit_collaborators',
            field=models.ManyToManyField(related_name='edit_access', to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AlterField(
            model_name='foiarequest',
            name='email',
            field=models.EmailField(max_length=254, blank=True),
        ),
        migrations.AlterField(
            model_name='foiarequest',
            name='embargo',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='foiarequest',
            name='featured',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='foiarequest',
            name='read_collaborators',
            field=models.ManyToManyField(related_name='read_access', to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AlterField(
            model_name='foiarequest',
            name='tracker',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='foiarequest',
            name='updated',
            field=models.BooleanField(default=False),
        ),
    ]
