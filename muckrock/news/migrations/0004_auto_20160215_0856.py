# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import easy_thumbnails.fields


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0003_auto_20150618_2306'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='image',
            field=easy_thumbnails.fields.ThumbnailerImageField(null=True, upload_to=b'news_images/%Y/%m/%d', blank=True),
        ),
        migrations.AlterField(
            model_name='photo',
            name='image',
            field=models.ImageField(upload_to=b'news_photos/%Y/%m/%d'),
        ),
    ]
