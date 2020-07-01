# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('foia', '0005_foiarequest_date_estimate'),
    ]

    operations = [
        migrations.AddField(
            model_name='foiarequest',
            name='access_key',
            field=models.CharField(max_length=255, blank=True),
        ),
    ]
