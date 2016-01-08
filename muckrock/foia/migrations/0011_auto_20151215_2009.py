# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foia', '0010_foiacommunication_thanks'),
    ]

    operations = [
        migrations.AlterField(
            model_name='foiarequest',
            name='date_due',
            field=models.DateField(db_index=True, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='foiarequest',
            name='date_submitted',
            field=models.DateField(db_index=True, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='foiarequest',
            name='status',
            field=models.CharField(db_index=True, max_length=10, choices=[(b'started', b'Draft'), (b'submitted', b'Processing'), (b'ack', b'Awaiting Acknowledgement'), (b'processed', b'Awaiting Response'), (b'appealing', b'Awaiting Appeal'), (b'fix', b'Fix Required'), (b'payment', b'Payment Required'), (b'rejected', b'Rejected'), (b'no_docs', b'No Responsive Documents'), (b'done', b'Completed'), (b'partial', b'Partially Completed'), (b'abandoned', b'Withdrawn')]),
        ),
        migrations.AlterField(
            model_name='foiarequest',
            name='title',
            field=models.CharField(max_length=255, db_index=True),
        ),
    ]
