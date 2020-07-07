# -*- coding: utf-8 -*-

# Django
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Holiday',
            fields=[
                (
                    'id',
                    models.AutoField(
                        verbose_name='ID',
                        serialize=False,
                        auto_created=True,
                        primary_key=True
                    )
                ),
                ('name', models.CharField(max_length=255)),
                (
                    'kind',
                    models.CharField(
                        max_length=8,
                        choices=[('date',
                                  'Date'), ('ord_wd', 'Ordinal Weekday'),
                                 ('easter', 'Easter'), ('election', 'Election')]
                    )
                ),
                (
                    'month',
                    models.PositiveSmallIntegerField(
                        blank=True,
                        help_text=
                        'Only used for date and ordinal weekday holidays',
                        null=True,
                        choices=[(1, 'January'), (2, 'February'), (3, 'March'),
                                 (4, 'April'), (5, 'May'), (6, 'June'),
                                 (7, 'July'), (8, 'August'), (9, 'September'),
                                 (10,
                                  'October'), (11,
                                               'November'), (12, 'December')]
                    )
                ),
                (
                    'day',
                    models.PositiveSmallIntegerField(
                        blank=True,
                        help_text='Only used for date holidays',
                        null=True,
                        choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6),
                                 (7, 7), (8, 8), (9, 9), (10, 10), (11, 11),
                                 (12, 12), (13, 13), (14, 14), (15,
                                                                15), (16, 16),
                                 (17, 17), (18, 18), (19, 19), (20,
                                                                20), (21, 21),
                                 (22, 22), (23, 23), (24, 24), (25,
                                                                25), (26, 26),
                                 (27, 27), (28, 28), (29, 29), (30,
                                                                30), (31, 31)]
                    )
                ),
                (
                    'weekday',
                    models.PositiveSmallIntegerField(
                        blank=True,
                        help_text='Only used for ordinal weekday holidays',
                        null=True,
                        choices=[(0, 'Monday'), (1, 'Tuesday'),
                                 (2, 'Wednesday'), (3, 'Thursday'),
                                 (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')]
                    )
                ),
                (
                    'num',
                    models.SmallIntegerField(
                        help_text='Only used for ordinal weekday holidays',
                        null=True,
                        blank=True
                    )
                ),
            ],
            options={},
            bases=(models.Model,),
        ),
    ]
