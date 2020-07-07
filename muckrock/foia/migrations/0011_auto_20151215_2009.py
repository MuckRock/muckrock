# -*- coding: utf-8 -*-

# Django
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
            field=models.CharField(
                db_index=True,
                max_length=10,
                choices=[('started', 'Draft'), ('submitted', 'Processing'),
                         ('ack', 'Awaiting Acknowledgement'),
                         ('processed', 'Awaiting Response'),
                         ('appealing',
                          'Awaiting Appeal'), ('fix', 'Fix Required'),
                         ('payment',
                          'Payment Required'), ('rejected', 'Rejected'),
                         ('no_docs',
                          'No Responsive Documents'), ('done', 'Completed'),
                         ('partial',
                          'Partially Completed'), ('abandoned', 'Withdrawn')]
            ),
        ),
        migrations.AlterField(
            model_name='foiarequest',
            name='title',
            field=models.CharField(max_length=255, db_index=True),
        ),
    ]
