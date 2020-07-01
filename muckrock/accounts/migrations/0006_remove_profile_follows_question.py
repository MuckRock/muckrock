# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_remove_profile_follows_foia'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='follows_question',
        ),
    ]
