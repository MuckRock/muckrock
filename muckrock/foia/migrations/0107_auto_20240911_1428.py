# Generated by Django 4.2 on 2024-09-11 18:28

# Django
from django.db import migrations


def set_embargo_status(apps, schema_editor):
    FOIARequest = apps.get_model("foia", "FOIARequest")
    FOIAComposer = apps.get_model("foia", "FOIAComposer")
    FOIASavedSearch = apps.get_model("foia", "FOIASavedSearch")

    FOIARequest.objects.filter(embargo=True, permanent_embargo=False).update(
        embargo_status="embargo"
    )
    FOIARequest.objects.filter(permanent_embargo=True).update(
        embargo_status="permanent"
    )

    FOIAComposer.objects.filter(embargo=True, permanent_embargo=False).update(
        embargo_status="embargo"
    )
    FOIAComposer.objects.filter(permanent_embargo=True).update(
        embargo_status="permanent"
    )

    FOIASavedSearch.objects.filter(embargo=True).update(embargo_status="embargo")


def reverse_embargo_status(apps, schema_editor):
    FOIARequest = apps.get_model("foia", "FOIARequest")
    FOIAComposer = apps.get_model("foia", "FOIAComposer")
    FOIASavedSearch = apps.get_model("foia", "FOIASavedSearch")

    FOIARequest.objects.filter(embargo_status="embargo").update(embargo=True)
    FOIARequest.objects.filter(embargo_status="permanent").update(
        embargo=True, permanent_embargo=True
    )
    FOIAComposer.objects.filter(embargo_status="embargo").update(embargo=True)
    FOIAComposer.objects.filter(embargo_status="permanent").update(
        embargo=True, permanent_embargo=True
    )

    FOIASavedSearch.objects.filter(embargo_status="embargo").update(embargo=True)


class Migration(migrations.Migration):

    dependencies = [
        ("foia", "0106_foiacomposer_embargo_status_and_more"),
    ]

    operations = [migrations.RunPython(set_embargo_status, reverse_embargo_status)]
