# Generated by Django 4.2 on 2023-09-11 14:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0007_auto_20181204_2207'),
    ]

    operations = [
        migrations.AddField(
            model_name='portal',
            name='disable_automation',
            field=models.BooleanField(default=False),
        ),
    ]