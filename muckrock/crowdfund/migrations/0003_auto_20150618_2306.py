# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crowdfund', '0002_auto_20150614_2154'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='foias',
            field=models.ManyToManyField(related_name='foias', to='foia.FOIARequest', blank=True),
        ),
    ]
