# -*- coding: utf-8 -*-


# Django
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

# Third Party
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("tags", "0001_initial"),
        ("qanda", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="question",
            name="tags",
            field=taggit.managers.TaggableManager(
                to="tags.Tag",
                through="tags.TaggedItemBase",
                blank=True,
                help_text="A comma-separated list of tags.",
                verbose_name="Tags",
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="question",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="answer",
            name="question",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="answers",
                to="qanda.Question",
            ),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name="answer",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
            preserve_default=True,
        ),
    ]
