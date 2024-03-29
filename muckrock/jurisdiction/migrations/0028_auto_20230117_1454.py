# Generated by Django 3.2.9 on 2023-01-17 19:54

# Django
from django.db import migrations


def populate_jurisdiction_page(apps, schema_editor):
    Law = apps.get_model("jurisdiction", "Law")
    JurisdictionPage = apps.get_model("jurisdiction", "JurisdictionPage")

    for law in Law.objects.all():
        JurisdictionPage.objects.create(
            jurisdiction=law.jurisdiction,
            content=law.law_analysis,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("jurisdiction", "0027_historicaljurisdictionpage_jurisdictionpage"),
    ]

    operations = [migrations.RunPython(populate_jurisdiction_page)]
