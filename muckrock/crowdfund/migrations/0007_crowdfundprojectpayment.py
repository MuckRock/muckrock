# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('crowdfund', '0006_crowdfundproject'),
    ]

    operations = [
        migrations.CreateModel(
            name='CrowdfundProjectPayment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, blank=True)),
                ('amount', models.DecimalField(max_digits=14, decimal_places=2)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('show', models.BooleanField(default=False)),
                ('crowdfund', models.ForeignKey(related_name='payments', to='crowdfund.CrowdfundProject')),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
