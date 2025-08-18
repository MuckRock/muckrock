from django.db import migrations


def split_product_stats(apps, schema_editor):
    HomePage = apps.get_model("core", "HomePage")
    obj = HomePage.objects.first()
    if not obj:
        return

    stats = getattr(obj, "product_stats", None) or {}

    obj.dlp_stats = stats.get("dataliberation", {})

    doccloud = stats.get("documentcloud", {})
    obj.documentcloud_stats = {
        "total_documents_public": doccloud.get("documents", 0),
        "total_notes_public": doccloud.get("notes", 0),
        "total_pages_public": doccloud.get("pages", 0),
    }

    obj.save(update_fields=["dlp_stats", "documentcloud_stats"])


def merge_back_to_product_stats(apps, schema_editor):
    HomePage = apps.get_model("core", "HomePage")
    obj = HomePage.objects.first()
    if not obj:
        return

    obj.product_stats = {
        "dataliberation": obj.dlp_stats or {},
        "documentcloud": {
            "documents": obj.documentcloud_stats.get("total_documents_public", 0),
            "notes": obj.documentcloud_stats.get("total_notes_public", 0),
            "pages": obj.documentcloud_stats.get("total_pages_public", 0),
        },
    }

    obj.save(update_fields=["product_stats"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_homepage_product_stats"),
    ]

    operations = [
        migrations.RunPython(split_product_stats, merge_back_to_product_stats),
    ]
