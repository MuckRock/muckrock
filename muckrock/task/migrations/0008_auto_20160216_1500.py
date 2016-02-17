# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('task', '0007_auto_20160119_2225'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='paymenttask',
            name='foia',
        ),
        migrations.RemoveField(
            model_name='paymenttask',
            name='task_ptr',
        ),
        migrations.RemoveField(
            model_name='paymenttask',
            name='user',
        ),
        migrations.AddField(
            model_name='snailmailtask',
            name='amount',
            field=models.DecimalField(default=0, max_digits=8, decimal_places=2),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='snailmailtask',
            name='user',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='snailmailtask',
            name='category',
            field=models.CharField(max_length=1, choices=[(b'a', b'Appeal'), (b'n', b'New'), (b'u', b'Update'), (b'f', b'Followup'), (b'p', b'Payment')]),
        ),
        migrations.DeleteModel(
            name='PaymentTask',
        ),
    ]
