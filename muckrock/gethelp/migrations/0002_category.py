from django.db import migrations, models


CATEGORIES = [
    ("managing", "Managing this request", 0),
    ("communications", "Communications and messages", 1),
    ("payments", "Checks and request payments", 2),
    ("documents", "Documents and files", 3),
    ("portals", "Agency portals and web forms", 4),
    ("appeals", "Appeals and public records advice", 5),
    ("proxy", "In-state proxy and proof of citizenship", 6),
]


def populate_categories(apps, schema_editor):
    Category = apps.get_model("gethelp", "Category")
    for slug, label, order in CATEGORIES:
        Category.objects.create(slug=slug, label=label, order=order)


class Migration(migrations.Migration):

    dependencies = [
        ("gethelp", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("slug", models.SlugField(unique=True)),
                ("label", models.CharField(max_length=100)),
                ("order", models.PositiveIntegerField(default=0)),
            ],
            options={
                "verbose_name_plural": "categories",
                "ordering": ["order"],
            },
        ),
        migrations.RunPython(populate_categories, migrations.RunPython.noop),
    ]
