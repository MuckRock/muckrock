# -*- coding: utf-8 -*-


# Django
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crowdfund", "0011_auto_20160127_1834"),
        ("task", "0007_auto_20160119_2225"),
    ]

    operations = [
        migrations.CreateModel(
            name="NewCrowdfundTask",
            fields=[
                (
                    "task_ptr",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        to="task.Task",
                    ),
                ),
                (
                    "crowdfund",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="crowdfund.Crowdfund",
                    ),
                ),
            ],
            bases=("task.task",),
        )
    ]
