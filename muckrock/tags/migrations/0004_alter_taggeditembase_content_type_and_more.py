# Generated by Django 4.2 on 2024-04-10 14:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("tags", "0003_auto_20200804_1309"),
    ]

    operations = [
        migrations.AlterField(
            model_name="taggeditembase",
            name="content_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(app_label)s_%(class)s_tagged_items",
                to="contenttypes.contenttype",
                verbose_name="content type",
            ),
        ),
        migrations.AlterField(
            model_name="taggeditembase",
            name="tag",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(app_label)s_%(class)s_items",
                to="tags.tag",
            ),
        ),
    ]
