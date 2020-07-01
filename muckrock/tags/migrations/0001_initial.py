# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('tag_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='taggit.Tag')),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=('taggit.tag',),
        ),
        migrations.CreateModel(
            name='TaggedItemBase',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.IntegerField(verbose_name='Object id', db_index=True)),
                ('content_type', models.ForeignKey(related_name='tags_taggeditembase_tagged_items', verbose_name='Content type', to='contenttypes.ContentType')),
                ('tag', models.ForeignKey(related_name='tags_taggeditembase_items', to='tags.Tag')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
