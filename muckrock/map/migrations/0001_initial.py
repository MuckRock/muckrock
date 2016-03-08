# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import djgeojson.fields


class Migration(migrations.Migration):

    dependencies = [
        ('foia', '0017_remove_foiarequest_location'),
    ]

    operations = [
        migrations.CreateModel(
            name='Map',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(unique=True, max_length=80)),
                ('slug', models.SlugField(unique=True, max_length=80)),
                ('description', models.TextField(blank=True)),
                ('private', models.BooleanField(default=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('center', djgeojson.fields.PointField(default={b'type': b'Point', b'coordinates': [39.83, -98.58]})),
                ('zoom', models.IntegerField(default=4)),
                ('project', models.ForeignKey(related_name='maps', to='project.Project')),
            ],
        ),
        migrations.CreateModel(
            name='Marker',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('point', djgeojson.fields.PointField(blank=True)),
                ('foia', models.ForeignKey(related_name='locations', to='foia.FOIARequest')),
                ('map', models.ForeignKey(related_name='markers', to='map.Map')),
            ],
        ),
    ]
