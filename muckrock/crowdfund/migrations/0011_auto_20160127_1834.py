# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('foia', '0013_auto_20151215_2035'),
        ('project', '0004_auto_20160127_1834'),
        ('crowdfund', '0010_auto_20151103_1520'),
    ]

    operations = [
        migrations.CreateModel(
            name='Crowdfund',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('payment_capped', models.BooleanField(default=False)),
                ('payment_required', models.DecimalField(default=b'0.00', max_digits=14, decimal_places=2)),
                ('payment_received', models.DecimalField(default=b'0.00', max_digits=14, decimal_places=2)),
                ('date_due', models.DateField()),
                ('closed', models.BooleanField(default=False)),
                ('foia', models.OneToOneField(related_name='crowdfund', null=True, blank=True, to='foia.FOIARequest')),
                ('project', models.ForeignKey(related_name='crowdfunds', blank=True, to='project.Project', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CrowdfundPayment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, blank=True)),
                ('amount', models.DecimalField(max_digits=14, decimal_places=2)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('show', models.BooleanField(default=False)),
                ('charge_id', models.CharField(max_length=255, blank=True)),
                ('crowdfund', models.ForeignKey(related_name='payments', to='crowdfund.Crowdfund')),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.AlterField(
            model_name='crowdfundrequest',
            name='foia',
            field=models.OneToOneField(to='foia.FOIARequest'),
        ),
    ]
