# Generated by Django 4.2 on 2023-06-09 13:09

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("foia", "0094_foiacommunication_category"),
    ]

    operations = [
        migrations.AddField(
            model_name="foianote",
            name="notify",
            field=models.BooleanField(default=False, help_text="Notify user"),
        ),
        migrations.AlterField(
            model_name="foiasavedsearch",
            name="users",
            field=models.ManyToManyField(related_name="+", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name="outboundcomposerattachment",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="pending_%(class)s",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="outboundrequestattachment",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="pending_%(class)s",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
