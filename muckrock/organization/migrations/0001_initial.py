# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('slug', models.SlugField(unique=True, max_length=255)),
                ('date_update', models.DateField()),
                ('num_requests', models.IntegerField(default=0)),
                ('max_users', models.IntegerField(default=50)),
                ('monthly_cost', models.IntegerField(default=45000)),
                ('monthly_requests', models.IntegerField(default=200)),
                ('stripe_id', models.CharField(max_length=255, blank=True)),
                ('active', models.BooleanField(default=False)),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
