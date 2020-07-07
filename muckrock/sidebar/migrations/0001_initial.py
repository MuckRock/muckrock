# -*- coding: utf-8 -*-

# Django
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Sidebar',
            fields=[
                (
                    'id',
                    models.AutoField(
                        verbose_name='ID',
                        serialize=False,
                        auto_created=True,
                        primary_key=True
                    )
                ),
                (
                    'title',
                    models.CharField(
                        unique=True,
                        max_length=255,
                        choices=[('admin', 'Admin'), ('beta', 'Beta'),
                                 ('community',
                                  'Community'), ('pro', 'Professional'),
                                 ('proxy', 'Proxy'), ('anonymous', 'Visitor')]
                    )
                ),
                ('text', models.TextField(blank=True)),
            ],
            options={},
            bases=(models.Model,),
        ),
    ]
