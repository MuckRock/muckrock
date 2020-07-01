# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0002_article_tags'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='editors',
            field=models.ManyToManyField(related_name='edited_articles', to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AlterField(
            model_name='article',
            name='foias',
            field=models.ManyToManyField(related_name='articles', to='foia.FOIARequest', blank=True),
        ),
    ]
