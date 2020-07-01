# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Holiday',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('kind', models.CharField(max_length=8, choices=[(b'date', b'Date'), (b'ord_wd', b'Ordinal Weekday'), (b'easter', b'Easter'), (b'election', b'Election')])),
                ('month', models.PositiveSmallIntegerField(blank=True, help_text=b'Only used for date and ordinal weekday holidays', null=True, choices=[(1, b'January'), (2, b'February'), (3, b'March'), (4, b'April'), (5, b'May'), (6, b'June'), (7, b'July'), (8, b'August'), (9, b'September'), (10, b'October'), (11, b'November'), (12, b'December')])),
                ('day', models.PositiveSmallIntegerField(blank=True, help_text=b'Only used for date holidays', null=True, choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10), (11, 11), (12, 12), (13, 13), (14, 14), (15, 15), (16, 16), (17, 17), (18, 18), (19, 19), (20, 20), (21, 21), (22, 22), (23, 23), (24, 24), (25, 25), (26, 26), (27, 27), (28, 28), (29, 29), (30, 30), (31, 31)])),
                ('weekday', models.PositiveSmallIntegerField(blank=True, help_text=b'Only used for ordinal weekday holidays', null=True, choices=[(0, b'Monday'), (1, b'Tuesday'), (2, b'Wednesday'), (3, b'Thursday'), (4, b'Friday'), (5, b'Saturday'), (6, b'Sunday')])),
                ('num', models.SmallIntegerField(help_text=b'Only used for ordinal weekday holidays', null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
