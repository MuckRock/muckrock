# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Sidebar',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(unique=True, max_length=255, choices=[(b'admin', b'Admin'), (b'beta', b'Beta'), (b'community', b'Community'), (b'pro', b'Professional'), (b'proxy', b'Proxy'), (b'anonymous', b'Visitor')])),
                ('text', models.TextField(blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
