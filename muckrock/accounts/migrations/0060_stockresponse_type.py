# Generated by Django 4.2 on 2023-12-19 13:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0059_stockresponse"),
    ]

    operations = [
        migrations.AddField(
            model_name="stockresponse",
            name="type",
            field=models.CharField(
                choices=[("user", "Contact User"), ("note", "Note")],
                default="user",
                max_length=4,
            ),
        ),
    ]
