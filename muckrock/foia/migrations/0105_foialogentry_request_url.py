# Generated by Django 4.2 on 2024-06-05 14:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("foia", "0104_alter_foialogentry_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="foialogentry",
            name="request_url",
            field=models.URLField(blank=True, max_length=255),
        ),
    ]