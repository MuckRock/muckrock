# -*- coding: utf-8 -*-

# Django
from django.db import migrations, models

# Third Party
import easy_thumbnails.fields


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0003_auto_20150618_2306'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='image',
            field=easy_thumbnails.fields.ThumbnailerImageField(
                null=True, upload_to='news_images/%Y/%m/%d', blank=True
            ),
        ),
        migrations.AlterField(
            model_name='photo',
            name='image',
            field=models.ImageField(upload_to='news_photos/%Y/%m/%d'),
        ),
    ]
