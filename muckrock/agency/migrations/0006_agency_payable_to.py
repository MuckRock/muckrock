# -*- coding: utf-8 -*-


# Django
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("agency", "0005_auto_20160210_1943")]

    operations = [
        migrations.AddField(
            model_name="agency",
            name="payable_to",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="receivable",
                blank=True,
                to="agency.Agency",
                null=True,
            ),
        )
    ]
