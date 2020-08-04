# -*- coding: utf-8 -*-


from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('organization', '0001_initial'),
        ('jurisdiction', '0001_initial'),
        ('accounts', '0002_profile_follows_foia'),
        ('qanda', '0001_initial'),
        ('foia', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='follows_question',
            field=models.ManyToManyField(related_name='followed_by', to='qanda.Question', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='profile',
            name='location',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, blank=True, to='jurisdiction.Jurisdiction', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='profile',
            name='notifications',
            field=models.ManyToManyField(related_name='notify', to='foia.FOIARequest', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='profile',
            name='organization',
            field=models.ForeignKey(related_name='members', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='organization.Organization', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='profile',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, unique=True),
            preserve_default=True,
        ),
    ]
