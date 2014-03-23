"""
Serilizers for the news application API
"""

from rest_framework import serializers

from muckrock.news.models import Article

# pylint: disable=R0903

class ArticleSerializer(serializers.ModelSerializer):
    """Serializer for Article model"""

    authors = serializers.RelatedField(many=True)
    editors = serializers.RelatedField(many=True)

    class Meta:
        model = Article
