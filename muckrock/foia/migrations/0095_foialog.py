# Generated by Django 3.2.9 on 2023-04-12 15:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0032_agency_use_portal_appeal'),
        ('foia', '0094_foiacommunication_category'),
    ]

    operations = [
        migrations.CreateModel(
            name='FOIALog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_id', models.CharField(max_length=255, unique=True)),
                ('requestor', models.CharField(max_length=255)),
                ('subject', models.TextField()),
                ('date', models.DateField()),
                ('agency', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='agency.agency')),
            ],
        ),
    ]
