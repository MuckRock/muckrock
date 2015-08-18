# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0001_initial'),
        ('crowdfund', '0005_auto_20150720_1132'),
    ]

    operations = [
        migrations.CreateModel(
            name='CrowdfundProject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('payment_required', models.DecimalField(default=b'0.00', max_digits=14, decimal_places=2)),
                ('payment_received', models.DecimalField(default=b'0.00', max_digits=14, decimal_places=2)),
                ('date_due', models.DateField()),
                ('project', models.ForeignKey(related_name='crowdfund', to='project.Project')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
