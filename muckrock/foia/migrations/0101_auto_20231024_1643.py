# Generated by Django 4.2 on 2023-10-24 20:43

# Django
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("foia", "0100_merge_20230911_1631"),
    ]

    operations = [migrations.DeleteModel("FOIALog")]
