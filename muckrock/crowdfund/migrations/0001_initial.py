# -*- coding: utf-8 -*-

# Django
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='CrowdfundProject',
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
                    'payment_required',
                    models.DecimalField(
                        default='0.00', max_digits=8, decimal_places=2
                    )
                ),
                (
                    'payment_received',
                    models.DecimalField(
                        default='0.00', max_digits=8, decimal_places=2
                    )
                ),
                ('date_due', models.DateField()),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CrowdfundProjectPayment',
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
                ('name', models.CharField(max_length=255, blank=True)),
                ('amount', models.DecimalField(max_digits=8, decimal_places=2)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('show', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CrowdfundRequest',
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
                    'payment_required',
                    models.DecimalField(
                        default='0.00', max_digits=8, decimal_places=2
                    )
                ),
                (
                    'payment_received',
                    models.DecimalField(
                        default='0.00', max_digits=8, decimal_places=2
                    )
                ),
                ('date_due', models.DateField()),
                (
                    'name',
                    models.CharField(
                        default='Crowdfund this request', max_length=255
                    )
                ),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CrowdfundRequestPayment',
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
                ('name', models.CharField(max_length=255, blank=True)),
                ('amount', models.DecimalField(max_digits=8, decimal_places=2)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('show', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Project',
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
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(max_length=255)),
                ('description', models.TextField(blank=True)),
            ],
            options={},
            bases=(models.Model,),
        ),
    ]
