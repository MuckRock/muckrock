# Generated by Django 2.2.15 on 2020-10-16 17:27

# Django
from django.db import migrations
from django.db.models.expressions import F
from django.db.models.functions.text import Length


def copy_mail_names(apps, schema_editor):
    """Copy agency name to mail name if it fits in 40 characters"""
    Agency = apps.get_model("agency", "agency")
    Agency.objects.annotate(name_length=Length("name")).filter(
        name_length__lte=40
    ).update(mail_name=F("name"))


class Migration(migrations.Migration):

    dependencies = [("agency", "0028_agency_mail_name")]

    operations = [migrations.RunPython(copy_mail_names, migrations.RunPython.noop)]