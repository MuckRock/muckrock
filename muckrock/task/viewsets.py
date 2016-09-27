"""
Viewsets for the Task API
"""

from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions
import django_filters

from muckrock.task.models import (
        Task, OrphanTask, SnailMailTask, RejectedEmailTask, StaleAgencyTask,
        FlaggedTask, NewAgencyTask, ResponseTask, NewExemptionTask, GenericTask)
from muckrock.task.serializers import (
        TaskSerializer, OrphanTaskSerializer, SnailMailTaskSerializer,
        RejectedEmailTaskSerializer, StaleAgencyTaskSerializer,
        FlaggedTaskSerializer, NewAgencyTaskSerializer, ResponseTaskSerializer,
        NewExemptionTaskSerializer, GenericTaskSerializer)

def create_task_viewset(model, serializer, fields):
    """Create a viewset for a task"""
    # pylint: disable=invalid-name
    Meta = type('Meta', (object,), {
        'model': model,
        'fields': (
            'min_date_created',
            'max_date_created',
            'min_date_done',
            'max_date_done',
            'resolved',
            'assigned') + fields
    })

    Filter = type('Filter', (django_filters.FilterSet,), dict(
        assigned=django_filters.CharFilter(name='assigned__username'),
        min_date_created=django_filters.DateFilter(name='date_created', lookup_type='gte'),
        max_date_created=django_filters.DateFilter(name='date_created', lookup_type='lte'),
        min_date_done=django_filters.DateFilter(name='date_done', lookup_type='gte'),
        max_date_done=django_filters.DateFilter(name='date_done', lookup_type='lte'),
        Meta=Meta,
    ))

    return type((model.__name__ + 'ViewSet'), (viewsets.ModelViewSet,), {
        'queryset': model.objects.all(),
        'serializer_class': serializer,
        'permission_classes': (DjangoModelPermissions,),
        'filter_class': Filter,
    })

TaskViewSet = create_task_viewset(
    Task,
    TaskSerializer,
    (),
)

OrphanTaskViewSet = create_task_viewset(
    OrphanTask,
    OrphanTaskSerializer,
    ('reason', 'communication', 'address'),
)

SnailMailTaskViewSet = create_task_viewset(
    SnailMailTask,
    SnailMailTaskSerializer,
    ('category', 'communication'),
)

RejectedEmailTaskViewSet = create_task_viewset(
    RejectedEmailTask,
    RejectedEmailTaskSerializer,
    ('category', 'foia', 'email', 'error'),
)

StaleAgencyTaskViewSet = create_task_viewset(
    StaleAgencyTask,
    StaleAgencyTaskSerializer,
    ('agency',),
)

FlaggedTaskViewSet = create_task_viewset(
    FlaggedTask,
    FlaggedTaskSerializer,
    ('user', 'text', 'foia', 'agency', 'jurisdiction'),
)

NewAgencyTaskViewSet = create_task_viewset(
    NewAgencyTask,
    NewAgencyTaskSerializer,
    ('user', 'agency'),
)

ResponseTaskViewSet = create_task_viewset(
    ResponseTask,
    ResponseTaskSerializer,
    ('communication',),
)

NewExemptionTaskViewSet = create_task_viewset(
    NewExemptionTask,
    NewExemptionTaskSerializer,
    ('user', 'foia', 'language'),
)

GenericTaskViewSet = create_task_viewset(
    GenericTask,
    GenericTaskSerializer,
    ('subject', 'body'),
)
