# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sidebar', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Sidebar',
            new_name='Broadcast',
        ),
        migrations.RenameField(
            model_name='broadcast',
            old_name='title',
            new_name='context',
        ),
    ]
