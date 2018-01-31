"""
Serilizers for the news application API
"""

# Third Party
from rest_framework import serializers

# MuckRock
from muckrock.foia.models import FOIARequest
from muckrock.news.models import Article


class ArticleSerializer(serializers.ModelSerializer):
    """Serializer for Article model"""

    authors = serializers.StringRelatedField(many=True)
    editors = serializers.StringRelatedField(many=True)
    foias = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=FOIARequest.objects.all(),
        style={
            'base_template': 'input.html'
        }
    )

    class Meta:
        model = Article
