import django.db.models.deletion
from django.db import migrations, models


def populate_category_fk(apps, schema_editor):
    Problem = apps.get_model("gethelp", "Problem")
    Category = apps.get_model("gethelp", "Category")
    category_map = {c.slug: c for c in Category.objects.all()}
    for problem in Problem.objects.all():
        problem.category_new = category_map[problem.category]
        problem.save(update_fields=["category_new"])


class Migration(migrations.Migration):

    dependencies = [
        ("gethelp", "0002_category"),
    ]

    operations = [
        migrations.AddField(
            model_name="problem",
            name="category_new",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="problems",
                to="gethelp.category",
            ),
        ),
        migrations.RunPython(populate_category_fk, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="problem",
            name="category",
        ),
        migrations.RenameField(
            model_name="problem",
            old_name="category_new",
            new_name="category",
        ),
        migrations.AlterField(
            model_name="problem",
            name="category",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="problems",
                to="gethelp.category",
            ),
        ),
        migrations.AlterModelOptions(
            name="problem",
            options={"ordering": ["category__order", "order"]},
        ),
    ]
