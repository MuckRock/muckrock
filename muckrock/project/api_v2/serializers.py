"""Serializers for Projects"""

# Third Party
from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers

# MuckRock
from muckrock.project.models import Project


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Project Example",
            value={
                "id": 11,
                "title": "Street Level Surveillance: Biometrics FOIA Campaign",
                "slug": "street-level-surveillance-biometrics-foia-campaign",
                "summary": "A project investigating biometric surveillance by law enforcement agencies.",
                "description": "Participation is simple! Fill in the form and we'll handle the rest.",
                "image": "https://cdn.muckrock.com/project_images/example.png",
                "private": False,
                "approved": True,
                "featured": False,
                "contributors": [167, 3647],
                "articles": [1736, 1272, 1235],
                "requests": [20203, 20202, 20229],
                "date_created": "2024-02-01T12:34:56Z",
                "date_approved": "2024-02-05T15:20:30Z",
            },
        )
    ]
)
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
        extra_kwargs = {
            "summary": {"help_text": "A brief summary of the project."},
            "description": {
                "help_text": "Detailed project description, supports HTML."
            },
            "image": {"help_text": "URL of the project’s cover image."},
            "private": {"help_text": "Whether the project is private or public."},
            "approved": {"help_text": "Indicates if the project has been approved."},
            "featured": {"help_text": "Marks the project as featured on MuckRock."},
            "contributors": {"help_text": "List of contributor user IDs."},
            "articles": {"help_text": "List of related article IDs."},
            "requests": {
                "help_text": "List of request IDs associated with this project."
            },
            "date_created": {"help_text": "The date the project was created."},
            "date_approved": {"help_text": "The date the project was approved."},
        }
