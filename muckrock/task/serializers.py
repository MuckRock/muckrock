"""
Serilizers for the task application API
"""

# Django
from django.contrib.auth.models import User

# Third Party
from rest_framework import serializers

# MuckRock
from muckrock.agency.models import Agency
from muckrock.foia.models import FOIACommunication, FOIARequest
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.task.models import (
    FlaggedTask,
    GenericTask,
    NewAgencyTask,
    NewExemptionTask,
    OrphanTask,
    ResponseTask,
    SnailMailTask,
    StaleAgencyTask,
    Task,
)


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model"""
    assigned = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), style={
            'base_template': 'input.html'
        }
    )
    orphantask = serializers.PrimaryKeyRelatedField(
        queryset=OrphanTask.objects.all(),
        style={
            'base_template': 'input.html'
        }
    )
    snailmailtask = serializers.PrimaryKeyRelatedField(
        queryset=SnailMailTask.objects.all(),
        style={
            'base_template': 'input.html'
        }
    )
    staleagencytask = serializers.PrimaryKeyRelatedField(
        queryset=StaleAgencyTask.objects.all(),
        style={
            'base_template': 'input.html'
        }
    )
    flaggedtask = serializers.PrimaryKeyRelatedField(
        queryset=FlaggedTask.objects.all(),
        style={
            'base_template': 'input.html'
        }
    )
    newagencytask = serializers.PrimaryKeyRelatedField(
        queryset=NewAgencyTask.objects.all(),
        style={
            'base_template': 'input.html'
        }
    )
    responsetask = serializers.PrimaryKeyRelatedField(
        queryset=ResponseTask.objects.all(),
        style={
            'base_template': 'input.html'
        }
    )
    newexemptiontask = serializers.PrimaryKeyRelatedField(
        queryset=NewExemptionTask.objects.all(),
        style={
            'base_template': 'input.html'
        }
    )

    class Meta:
        model = Task
        fields = (
            'id', 'date_created', 'date_done', 'resolved', 'assigned',
            'orphantask', 'snailmailtask', 'rejectedemailtask',
            'staleagencytask', 'flaggedtask', 'newagencytask', 'responsetask',
            'newexemptiontask'
        )


class OrphanTaskSerializer(serializers.ModelSerializer):
    """Serializer for OrphanTask model"""
    assigned = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), style={
            'base_template': 'input.html'
        }
    )
    resolved_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), style={
            'base_template': 'input.html'
        }
    )
    communication = serializers.PrimaryKeyRelatedField(
        queryset=FOIACommunication.objects.all(),
        style={
            'base_template': 'input.html'
        }
    )

    class Meta:
        model = OrphanTask


class SnailMailTaskSerializer(serializers.ModelSerializer):
    """Serializer for SnailMailTask model"""
    assigned = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), style={
            'base_template': 'input.html'
        }
    )
    resolved_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), style={
            'base_template': 'input.html'
        }
    )
    communication = serializers.PrimaryKeyRelatedField(
        queryset=FOIACommunication.objects.all(),
        style={
            'base_template': 'input.html'
        }
    )
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), style={
            'base_template': 'input.html'
        }
    )

    class Meta:
        model = SnailMailTask


class StaleAgencyTaskSerializer(serializers.ModelSerializer):
    """Serializer for StaleAgencyTask model"""
    assigned = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), style={
            'base_template': 'input.html'
        }
    )
    resolved_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), style={
            'base_template': 'input.html'
        }
    )
    agency = serializers.PrimaryKeyRelatedField(
        queryset=Agency.objects.all(), style={
            'base_template': 'input.html'
        }
    )

    class Meta:
        model = StaleAgencyTask


class FlaggedTaskSerializer(serializers.ModelSerializer):
    """Serializer for FlaggedTask model"""
    assigned = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), style={
            'base_template': 'input.html'
        }
    )
    resolved_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), style={
            'base_template': 'input.html'
        }
    )
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), style={
            'base_template': 'input.html'
        }
    )
    foia = serializers.PrimaryKeyRelatedField(
        queryset=FOIARequest.objects.all(),
        style={
            'base_template': 'input.html'
        }
    )
    agency = serializers.PrimaryKeyRelatedField(
        queryset=Agency.objects.all(), style={
            'base_template': 'input.html'
        }
    )
    jurisdiction = serializers.PrimaryKeyRelatedField(
        queryset=Jurisdiction.objects.all(),
        style={
            'base_template': 'input.html'
        }
    )

    class Meta:
        model = FlaggedTask


class NewAgencyTaskSerializer(serializers.ModelSerializer):
    """Serializer for NewAgencyTask model"""
    assigned = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), style={
            'base_template': 'input.html'
        }
    )
    resolved_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), style={
            'base_template': 'input.html'
        }
    )
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), style={
            'base_template': 'input.html'
        }
    )
    agency = serializers.PrimaryKeyRelatedField(
        queryset=Agency.objects.all(), style={
            'base_template': 'input.html'
        }
    )

    class Meta:
        model = NewAgencyTask


class ResponseTaskSerializer(serializers.ModelSerializer):
    """Serializer for ResponseTask model"""
    assigned = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), style={
            'base_template': 'input.html'
        }
    )
    resolved_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), style={
            'base_template': 'input.html'
        }
    )
    communication = serializers.PrimaryKeyRelatedField(
        queryset=FOIACommunication.objects.all(),
        style={
            'base_template': 'input.html'
        }
    )

    class Meta:
        model = ResponseTask


class NewExemptionTaskSerializer(serializers.ModelSerializer):
    """Serializer for NewExemptionTask model"""
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), style={
            'base_template': 'input.html'
        }
    )
    foia = serializers.PrimaryKeyRelatedField(
        queryset=FOIARequest.objects.all(),
        style={
            'base_template': 'input.html'
        }
    )

    class Meta:
        model = NewExemptionTask


class GenericTaskSerializer(serializers.ModelSerializer):
    """Serializer for GenericTask model"""

    class Meta:
        model = GenericTask
