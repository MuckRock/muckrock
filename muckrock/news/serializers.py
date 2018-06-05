"""
Serilizers for the news application API
"""

# Django
from django.contrib.auth.models import User

# Third Party
from rest_framework import serializers

# MuckRock
from muckrock.foia.models import FOIARequest
from muckrock.news.models import Article, Photo


class ArticleSerializer(serializers.ModelSerializer):
    """Serializer for Article model"""

    authors = serializers.SlugRelatedField(
        many=True,
        slug_field='username',
        queryset=User.objects.all(),
    )
    editors = serializers.SlugRelatedField(
        many=True,
        slug_field='username',
        queryset=User.objects.all(),
    )
    foias = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=FOIARequest.objects.all(),
        style={
            'base_template': 'input.html'
        }
    )

    class Meta:
        model = Article


class PhotoSerializer(serializers.ModelSerializer):
    """Serializer for Photo model"""

    class Meta:
        model = Photo
