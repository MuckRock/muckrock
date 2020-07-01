# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('jurisdiction', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jurisdiction',
            name='observe_sat',
            field=models.BooleanField(default=False, help_text=b'Are holidays observed on Saturdays? (or are they moved to Friday?)'),
        ),
    ]
