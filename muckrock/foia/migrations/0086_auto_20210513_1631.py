# Generated by Django 2.2.15 on 2021-05-13 20:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foia', '0085_foiatemplate_jurisdiction'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='foiatemplate',
            options={'verbose_name': 'FOIA Template'},
        ),
        migrations.AlterField(
            model_name='foiatemplate',
            name='name',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
