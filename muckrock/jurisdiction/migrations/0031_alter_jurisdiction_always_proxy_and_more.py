# Generated by Django 4.2 on 2025-02-04 15:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jurisdiction', '0030_historicaljurisdictionpage_updated_at_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jurisdiction',
            name='always_proxy',
            field=models.BooleanField(default=False, help_text='Agencies in this jurisdiction should always be filed with a proxy'),
        ),
        migrations.AlterField(
            model_name='law',
            name='requires_proxy',
            field=models.BooleanField(default=False, help_text="This marks that this jurisdiction's law has a citizenshiprequirement.  It is used for informational purposes.  Agencies can bemarked individually to use the proxy system, in the case that this isnot widely enforced.  If it is widely enforced and you would like touse the proxy system for all agencies, please use the `Always Proxy`option under the State/Federal option section"),
        ),
    ]
