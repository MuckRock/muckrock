# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rejectedemailtask',
            name='email',
            field=models.EmailField(max_length=254, blank=True),
        ),
    ]
