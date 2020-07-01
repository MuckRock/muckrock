# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_auto_20151130_1759'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='payment_failed',
            field=models.BooleanField(default=False),
        ),
    ]
