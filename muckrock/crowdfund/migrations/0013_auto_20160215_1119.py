# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def convert_crowdfunds(apps, schema_editor):
    Crowdfund = apps.get_model('crowdfund', 'Crowdfund')
    CrowdfundRequest = apps.get_model('crowdfund', 'CrowdfundRequest')
    CrowdfundProject = apps.get_model('crowdfund', 'CrowdfundProject')
    CrowdfundPayment = apps.get_model('crowdfund', 'CrowdfundPayment')
    CrowdfundRequestPayment = apps.get_model('crowdfund', 'CrowdfundRequestPayment')
    CrowdfundProjectPayment = apps.get_model('crowdfund', 'CrowdfundProjectPayment')
    FOIARequest = apps.get_model('foia', 'FOIARequest')
    Project = apps.get_model('project', 'Project')
    ProjectCrowdfunds = apps.get_model('project', 'ProjectCrowdfunds')

    for cfr in CrowdfundRequest.objects.all():
        cf = Crowdfund.objects.create(
                name=cfr.name,
                description=cfr.description,
                payment_capped=cfr.payment_capped,
                payment_required=cfr.payment_required,
                payment_received=cfr.payment_received,
                date_due=cfr.date_due,
                closed=cfr.closed,
                )
        cfr.foia.crowdfund = cf
        cfr.foia.save()
        for payment in cfr.payments.all():
            CrowdfundPayment.objects.create(
                    user=payment.user,
                    name=payment.name,
                    amount=payment.amount,
                    date=payment.date,
                    show=payment.show,
                    charge_id=payment.charge_id,
                    crowdfund=cf,
                    )

    for cfp in CrowdfundProject.objects.all():
        cf = Crowdfund.objects.create(
                name=cfp.name,
                description=cfp.description,
                payment_capped=cfp.payment_capped,
                payment_required=cfp.payment_required,
                payment_received=cfp.payment_received,
                date_due=cfp.date_due,
                closed=cfp.closed,
                )
        project = cfp.project
        ProjectCrowdfunds.objects.create(project=project, crowdfund=cf)
        for payment in cfp.payments.all():
            CrowdfundPayment.objects.create(
                    user=payment.user,
                    name=payment.name,
                    amount=payment.amount,
                    date=payment.date,
                    show=payment.show,
                    charge_id=payment.charge_id,
                    crowdfund=cf,
                    )

def delete_crowdfunds(apps, schema_editor):
    Crowdfund = apps.get_model('crowdfund', 'Crowdfund')
    CrowdfundPayment = apps.get_model('crowdfund', 'CrowdfundPayment')
    ProjectCrowdfunds = apps.get_model('project', 'ProjectCrowdfunds')

    CrowdfundPayment.objects.all().delete()
    ProjectCrowdfunds.objects.all().delete()
    Crowdfund.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('crowdfund', '0012_auto_20160215_0856'),
        ('foia', '0014_foiarequest_crowdfund'),
        ('project', '0005_auto_20160215_0856'),
    ]

    operations = [
            migrations.RunPython(convert_crowdfunds, delete_crowdfunds),
    ]
