# Generated by Django 3.2.9 on 2022-10-19 13:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('communication', '0028_alter_source_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='source',
            name='type',
            field=models.CharField(choices=[('phone', 'Phone'), ('web', 'Web'), ('user', 'User'), ('request', 'Request')], max_length=7),
        ),
    ]
