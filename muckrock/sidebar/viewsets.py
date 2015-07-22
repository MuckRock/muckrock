"""
Viewsets for the Sidebar API
"""
from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions
from muckrock.sidebar.models import Sidebar
from muckrock.sidebar.serializers import SidebarSerializer

class SidebarViewSet(viewsets.ModelViewSet):
    """API views for Sidebar"""
    queryset = Sidebar.objects.all()
    serializer_class = SidebarSerializer
    permission_classes = (DjangoModelPermissions)
    filter_fields = ('title')
