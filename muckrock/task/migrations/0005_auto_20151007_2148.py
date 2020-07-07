# -*- coding: utf-8 -*-

# Django
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0004_responsetask_created_from_orphan'),
    ]

    operations = [
        migrations.AddField(
            model_name='responsetask',
            name='predicted_status',
            field=models.CharField(
                blank=True,
                max_length=10,
                null=True,
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
        migrations.AddField(
            model_name='responsetask',
            name='status_probability',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
