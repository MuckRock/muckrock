"""
Serilizers for the sidebar application API
"""
from rest_framework import serializers
from muckrock.sidebar.models import Sidebar

class SidebarSerializer(serializers.ModelSerializer):
    """Serializer for Sidebar model"""
    class Meta:
        model = Sidebar