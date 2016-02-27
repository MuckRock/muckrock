# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import migrations, models


def convert_tasks(apps, schema_editor):
    Crowdfund = apps.get_model('crowdfund', 'Crowdfund')
    CrowdfundRequest = apps.get_model('crowdfund', 'CrowdfundRequest')
    CrowdfundProject = apps.get_model('crowdfund', 'CrowdfundProject')
    FOIARequest = apps.get_model('foia', 'FOIARequest')
    Project = apps.get_model('project', 'Project')

    CrowdfundTask = apps.get_model('task', 'CrowdfundTask')
    GenericCrowdfundTask = apps.get_model('task', 'GenericCrowdfundTask')
    NewCrowdfundTask = apps.get_model('task', 'NewCrowdfundTask')

    # convert old foia only crowdfund tasks
    for cft in CrowdfundTask.objects.all():
        foia = cft.crowdfund.foia
        cf = Crowdfund.objects.get(foia=foia)
        NewCrowdfundTask.objects.create(
                crowdfund=cf,
                date_created=cft.date_created,
                date_done=cft.date_done,
                resolved=cft.resolved,
                assigned=cft.assigned,
                resolved_by=cft.resolved_by,
                )

    # convert generic crowdfund tasks
    for gcft in GenericCrowdfundTask.objects.all():
        ct = ContentType.objects.get(pk=gcft.content_type_id)
        if ct.model == 'crowdfundrequest':
            try:
                foia = CrowdfundRequest.objects.get(pk=gcft.object_id).foia
                cf = Crowdfund.objects.get(foia=foia)
                NewCrowdfundTask.objects.create(
                        crowdfund=cf,
                        date_created=gcft.date_created,
                        date_done=gcft.date_done,
                        resolved=gcft.resolved,
                        assigned=gcft.assigned,
                        resolved_by=gcft.resolved_by,
                        )
            except ObjectDoesNotExist as e:
                print '***error', gcft.pk, e
        elif ct.model == 'crowdfundproject':
            try:
                cfp = CrowdfundProject.objects.get(pk=gcft.object_id)
                project = cfp.project
                cf = Crowdfund.objects.get(
                        projects=project,
                        name=cfp.name,
                        description=cfp.description,
                        payment_capped=cfp.payment_capped,
                        payment_required=cfp.payment_required,
                        )
                NewCrowdfundTask.objects.create(
                        crowdfund=cf,
                        date_created=gcft.date_created,
                        date_done=gcft.date_done,
                        resolved=gcft.resolved,
                        assigned=gcft.assigned,
                        resolved_by=gcft.resolved_by,
                        )
            except ObjectDoesNotExist as e:
                print '***error', gcft.pk, e
        else:
            assert False, ct.model


def delete_new_cf_tasks(apps, schema_editor):
    NewCrowdfundTask = apps.get_model('task', 'NewCrowdfundTask')
    NewCrowdfundTask.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0008_newcrowdfundtask'),
        ('crowdfund', '0013_auto_20160215_1119'),
        ('foia', '0014_foiarequest_crowdfund'),
        ('project', '0005_auto_20160215_0856'),
    ]

    operations = [
            migrations.RunPython(convert_tasks, delete_new_cf_tasks),
    ]
