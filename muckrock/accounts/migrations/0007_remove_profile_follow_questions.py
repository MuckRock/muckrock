# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_remove_profile_follows_question'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='follow_questions',
        ),
    ]
