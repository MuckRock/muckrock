# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('agency', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agency',
            name='approved',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='agency',
            name='can_email_appeals',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='agency',
            name='email',
            field=models.EmailField(max_length=254, blank=True),
        ),
    ]
