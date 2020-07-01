# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('tags', '0001_initial'),
        ('foia', '0003_auto_20150618_2306'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('news', '0003_auto_20150618_2306'),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(help_text=b'Titles are limited to 100 characters.', unique=True, max_length=100)),
                ('slug', models.SlugField(help_text=b'The slug is automatically generated based on the title.', unique=True, max_length=255)),
                ('description', models.TextField(null=True, blank=True)),
                ('image', models.ImageField(null=True, upload_to=b'project_images', blank=True)),
                ('private', models.BooleanField(default=False, help_text=b'If a project is private, it is only visible to its contributors.')),
                ('articles', models.ManyToManyField(related_name='projects', to='news.Article', blank=True)),
                ('contributors', models.ManyToManyField(related_name='projects', to=settings.AUTH_USER_MODEL, blank=True)),
                ('requests', models.ManyToManyField(related_name='projects', to='foia.FOIARequest', blank=True)),
                ('tags', taggit.managers.TaggableManager(to='tags.Tag', through='tags.TaggedItemBase', blank=True, help_text='A comma-separated list of tags.', verbose_name='Tags')),
            ],
        ),
    ]
