# -*- coding: utf-8 -*-


# Django
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("foia", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="Answer",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("date", models.DateTimeField()),
                ("answer", models.TextField()),
            ],
            options={"ordering": ["date"]},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name="Question",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("slug", models.SlugField(max_length=255)),
                ("question", models.TextField()),
                ("date", models.DateTimeField()),
                ("answer_date", models.DateTimeField(null=True, blank=True)),
                (
                    "foia",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        blank=True,
                        to="foia.FOIARequest",
                        null=True,
                    ),
                ),
            ],
            options={"ordering": ["-date"]},
            bases=(models.Model,),
        ),
    ]
