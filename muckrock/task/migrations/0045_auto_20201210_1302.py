# Generated by Django 2.2.15 on 2020-12-10 18:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0044_auto_20200804_1309'),
    ]

    operations = [
        migrations.AlterField(
            model_name='snailmailtask',
            name='reason',
            field=models.CharField(blank=True, choices=[('auto', 'Automatic Lob sending was disabled'), ('addr', 'FOIA had no address'), ('badadd', 'Address field too long for Lob'), ('appeal', 'This is an appeal'), ('pay', 'This is a payment'), ('limit', 'Over the payment limit'), ('pdf', 'There was an error processing the PDF'), ('page', 'The PDF was over the page limit'), ('attm', 'There was an error processing an attachment'), ('lob', 'There was an error sending via Lob')], help_text='Reason the snail mail task was created instead of auto sending via lob', max_length=6),
        ),
    ]
