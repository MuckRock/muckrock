"""
ViewSets for FOIA Coach API
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from apps.jurisdiction.models import JurisdictionResource
from apps.jurisdiction.services.muckrock_client import MuckRockAPIClient
from apps.jurisdiction.services.gemini_service import GeminiFileSearchService
from .serializers import (
    JurisdictionSerializer,
    JurisdictionResourceSerializer,
    QueryRequestSerializer,
    QueryResponseSerializer,
)


class JurisdictionViewSet(viewsets.ViewSet):
    """
    ViewSet for accessing jurisdiction data from MuckRock API.
    Read-only access to state-level jurisdictions.
    """
    serializer_class = JurisdictionSerializer

    def list(self, request):
        """List all state jurisdictions from MuckRock API"""
        client = MuckRockAPIClient()
        try:
            jurisdictions = client.get_jurisdictions(level='s')
            serializer = JurisdictionSerializer(jurisdictions, many=True)
            return Response({
                'count': len(serializer.data),
                'results': serializer.data
            })
        except Exception as exc:
            return Response(
                {'error': f'Failed to fetch jurisdictions: {str(exc)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    def retrieve(self, request, pk=None):
        """
        Retrieve a single jurisdiction by abbreviation.
        pk is the abbreviation (e.g., 'CO', 'GA')
        """
        client = MuckRockAPIClient()
        try:
            jurisdiction = client.get_jurisdiction(pk)
            if not jurisdiction:
                return Response(
                    {'error': f'Jurisdiction {pk} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            serializer = JurisdictionSerializer(jurisdiction)
            return Response(serializer.data)
        except Exception as exc:
            return Response(
                {'error': f'Failed to fetch jurisdiction: {str(exc)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class JurisdictionResourceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for JurisdictionResource model.
    Read-only for now (can be extended to support CRUD later).
    """
    serializer_class = JurisdictionResourceSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['jurisdiction_id', 'jurisdiction_abbrev', 'resource_type', 'index_status', 'is_active']
    ordering_fields = ['created_at', 'updated_at', 'order', 'display_name']
    ordering = ['jurisdiction_abbrev', 'order', 'display_name']

    def get_queryset(self):
        """Return active resources by default"""
        queryset = JurisdictionResource.objects.filter(is_active=True)
        return queryset


class QueryViewSet(viewsets.ViewSet):
    """
    ViewSet for RAG query operations using Gemini File Search.
    """

    @action(detail=False, methods=['post'])
    def query(self, request):
        """
        Execute a RAG query against jurisdiction resources.

        Request body:
        {
            "question": "What is the response time in Colorado?",
            "state": "CO",  # optional
            "context": {},  # optional additional context
            "model": "gemini-2.0-flash-live"  # optional model selection
        }
        """
        serializer = QueryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question = serializer.validated_data['question']
        state = serializer.validated_data.get('state')
        context = serializer.validated_data.get('context')
        model = serializer.validated_data.get('model')

        try:
            service = GeminiFileSearchService()
            result = service.query(
                question=question,
                state=state,
                context=context,
                model=model
            )

            response_serializer = QueryResponseSerializer(result)
            return Response(response_serializer.data)

        except Exception as exc:
            return Response(
                {
                    'error': f'Query failed: {str(exc)}',
                    'question': question,
                    'state': state
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
