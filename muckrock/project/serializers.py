"""Serializers for Projects"""
# Third Party
from rest_framework import serializers

# MuckRock
from muckrock.project.models import Project


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for Project model"""

    class Meta:
        model = Project
        fields = [
            "id",
            "title",
            "slug",
            "summary",
            "description",
            "image",
            "private",
            "approved",
            "featured",
            "contributors",
            "articles",
            "requests",
            "date_created",
            "date_approved",
        ]
        extra_kwargs = {"contributors": {"style": {"base_template": "input.html"}}}
