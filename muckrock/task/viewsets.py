"""
Viewsets for the Task API
"""

# Third Party
import django_filters
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser

# MuckRock
from muckrock.task.models import (
    FlaggedTask,
    NewAgencyTask,
    OrphanTask,
    ResponseTask,
    SnailMailTask,
    Task,
)
from muckrock.task.serializers import (
    FlaggedTaskSerializer,
    NewAgencyTaskSerializer,
    OrphanTaskSerializer,
    ResponseTaskSerializer,
    SnailMailTaskSerializer,
    TaskSerializer,
)


def create_task_viewset(model, serializer, fields):
    """Create a viewset for a task"""
    Meta = type(
        "Meta",
        (object,),
        {
            "model": model,
            "fields": (
                "min_date_created",
                "max_date_created",
                "min_date_done",
                "max_date_done",
                "resolved",
                "assigned",
            )
            + fields,
        },
    )

    filter_fields = dict(
        assigned=django_filters.CharFilter(field_name="assigned__username"),
        min_date_created=django_filters.DateFilter(
            field_name="date_created", lookup_expr="gte"
        ),
        max_date_created=django_filters.DateFilter(
            field_name="date_created", lookup_expr="lte"
        ),
        min_date_done=django_filters.DateFilter(
            field_name="date_done", lookup_expr="gte"
        ),
        max_date_done=django_filters.DateFilter(
            field_name="date_done", lookup_expr="lte"
        ),
        Meta=Meta,
    )
    relation_fields = ["user", "foia", "communication", "agency", "jurisdiction"]
    for rfield in relation_fields:
        if rfield in fields:
            filter_fields[rfield] = django_filters.NumberFilter(
                field_name="%s__id" % rfield
            )
    Filter = type("Filter", (django_filters.FilterSet,), filter_fields)

    return type(
        (model.__name__ + "ViewSet"),
        (viewsets.ModelViewSet,),
        {
            "queryset": model.objects.all(),
            "serializer_class": serializer,
            "permission_classes": (IsAdminUser,),
            "filterset_class": Filter,
        },
    )


TaskViewSet = create_task_viewset(Task, TaskSerializer, ())

OrphanTaskViewSet = create_task_viewset(
    OrphanTask, OrphanTaskSerializer, ("reason", "communication", "address")
)

SnailMailTaskViewSet = create_task_viewset(
    SnailMailTask, SnailMailTaskSerializer, ("category", "communication")
)

FlaggedTaskViewSet = create_task_viewset(
    FlaggedTask,
    FlaggedTaskSerializer,
    ("user", "text", "foia", "agency", "jurisdiction"),
)

NewAgencyTaskViewSet = create_task_viewset(
    NewAgencyTask, NewAgencyTaskSerializer, ("user", "agency")
)

ResponseTaskViewSet = create_task_viewset(
    ResponseTask, ResponseTaskSerializer, ("communication",)
)
