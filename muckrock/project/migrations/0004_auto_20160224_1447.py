# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foia', '0015_foiarequest_location'),
        ('project', '0003_project_featured'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectMap',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(help_text=b'Titles are limited to 100 characters.', max_length=100)),
                ('description', models.TextField(null=True, blank=True)),
            ],
        ),
        migrations.AlterField(
            model_name='project',
            name='image',
            field=models.ImageField(null=True, upload_to=b'project_images/%Y/%m/%d', blank=True),
        ),
        migrations.AddField(
            model_name='projectmap',
            name='project',
            field=models.ForeignKey(related_name='maps', to='project.Project'),
        ),
        migrations.AddField(
            model_name='projectmap',
            name='requests',
            field=models.ManyToManyField(related_name='maps', to='foia.FOIARequest', blank=True),
        ),
    ]
