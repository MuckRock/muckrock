from django.db import migrations

CATEGORIES = [
    "Abusive Language to Agencies",
    "Abusive Language to Staff",
    "Requesting Private Information",
    "Taking Request off Platform",
    "Gangstalker",
    "Accusations in Request",
    "Complex",
    "Excessive irrelevant information",
    "BWC Footage",
]


def create_note_categories(apps, schema_editor):
    NoteCategory = apps.get_model("accounts", "NoteCategory")
    for name in CATEGORIES:
        NoteCategory.objects.get_or_create(name=name)


def remove_note_categories(apps, schema_editor):
    NoteCategory = apps.get_model("accounts", "NoteCategory")
    NoteCategory.objects.filter(name__in=CATEGORIES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0067_internalnote_category"),
    ]

    operations = [
        migrations.RunPython(create_note_categories, remove_note_categories),
    ]
