# Generated by Django 2.2.15 on 2021-03-25 18:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0055_auto_20200901_1327'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='preferred_proxy',
        ),
        migrations.AddField(
            model_name='profile',
            name='proxy',
            field=models.BooleanField(default=False, help_text='This user is a proxy filer for their home state'),
        ),
    ]
