# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0004_responsetask_created_from_orphan'),
    ]

    operations = [
        migrations.AddField(
            model_name='responsetask',
            name='predicted_status',
            field=models.CharField(blank=True, max_length=10, null=True, choices=[(b'started', b'Draft'), (b'submitted', b'Processing'), (b'ack', b'Awaiting Acknowledgement'), (b'processed', b'Awaiting Response'), (b'appealing', b'Awaiting Appeal'), (b'fix', b'Fix Required'), (b'payment', b'Payment Required'), (b'rejected', b'Rejected'), (b'no_docs', b'No Responsive Documents'), (b'done', b'Completed'), (b'partial', b'Partially Completed'), (b'abandoned', b'Withdrawn')]),
        ),
        migrations.AddField(
            model_name='responsetask',
            name='status_probability',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
