# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crowdfund', '0012_auto_20160215_0856'),
        ('project', '0004_auto_20160127_1834'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectCrowdfunds',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('crowdfund', models.OneToOneField(to='crowdfund.Crowdfund')),
                ('project', models.ForeignKey(to='project.Project')),
            ],
        ),
        migrations.AddField(
            model_name='project',
            name='crowdfunds',
            field=models.ManyToManyField(related_name='projects', through='project.ProjectCrowdfunds', to='crowdfund.Crowdfund'),
        ),
    ]
