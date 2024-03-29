# Generated by Django 3.2.9 on 2022-08-09 17:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('communication', '0025_emailopen_event'),
    ]

    operations = [
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField()),
                ('type', models.CharField(choices=[('phone', 'Phone'), ('web', 'Web'), ('user', 'User')], max_length=5)),
                ('url', models.URLField(blank=True, max_length=255)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sources', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='address',
            name='sources',
            field=models.ManyToManyField(related_name='addresses', to='communication.Source'),
        ),
        migrations.AddField(
            model_name='emailaddress',
            name='sources',
            field=models.ManyToManyField(related_name='emails', to='communication.Source'),
        ),
        migrations.AddField(
            model_name='phonenumber',
            name='sources',
            field=models.ManyToManyField(related_name='phones', to='communication.Source'),
        ),
    ]
