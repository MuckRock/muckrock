# -*- coding: utf-8 -*-


# Django
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("crowdfund", "0012_auto_20160215_0856"),
        ("foia", "0013_auto_20151215_2035"),
    ]

    operations = [
        migrations.AddField(
            model_name="foiarequest",
            name="crowdfund",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="foia",
                null=True,
                blank=True,
                to="crowdfund.Crowdfund",
            ),
        )
    ]
