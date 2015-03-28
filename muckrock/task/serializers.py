"""
Serilizers for the task application API
"""

from rest_framework import serializers

from muckrock.task.models import (
        Task, OrphanTask, SnailMailTask, RejectedEmailTask, StaleAgencyTask,
        FlaggedTask, NewAgencyTask, ResponseTask)

class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model"""

    class Meta:
        model = Task
        fields = ('id', 'date_created', 'date_done', 'resolved', 'assigned',
                  'orphantask', 'snailmailtask', 'rejectedemailtask',
                  'staleagencytask', 'flaggedtask', 'newagencytask',
                  'responsetask')


class OrphanTaskSerializer(serializers.ModelSerializer):
    """Serializer for OrphanTask model"""

    class Meta:
        model = OrphanTask


class SnailMailTaskSerializer(serializers.ModelSerializer):
    """Serializer for SnailMailTask model"""

    class Meta:
        model = SnailMailTask


class RejectedEmailTaskSerializer(serializers.ModelSerializer):
    """Serializer for RejectedEmailTask model"""

    class Meta:
        model = RejectedEmailTask


class StaleAgencyTaskSerializer(serializers.ModelSerializer):
    """Serializer for StaleAgencyTask model"""

    class Meta:
        model = StaleAgencyTask


class FlaggedTaskSerializer(serializers.ModelSerializer):
    """Serializer for FlaggedTask model"""

    class Meta:
        model = FlaggedTask


class NewAgencyTaskSerializer(serializers.ModelSerializer):
    """Serializer for NewAgencyTask model"""

    class Meta:
        model = NewAgencyTask


class ResponseTaskSerializer(serializers.ModelSerializer):
    """Serializer for ResponseTask model"""

    class Meta:
        model = ResponseTask
