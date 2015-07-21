"""
Serilizers for the news application API
"""

from django.contrib.auth.models import User

from rest_framework import serializers

from muckrock.news.models import Article

# pylint: disable=too-few-public-methods

class ArticleSerializer(serializers.ModelSerializer):
    """Serializer for Article model"""

    authors = serializers.RelatedField(many=True, queryset=User.objects.all())
    editors = serializers.RelatedField(many=True, queryset=User.objects.all())

    class Meta:
        model = Article
