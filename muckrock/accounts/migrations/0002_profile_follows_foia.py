# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('foia', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='follows_foia',
            field=models.ManyToManyField(related_name='followed_by', to='foia.FOIARequest', blank=True),
            preserve_default=True,
        ),
    ]
