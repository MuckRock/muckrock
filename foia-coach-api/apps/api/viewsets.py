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

    @action(detail=False, methods=['get'])
    def status(self, request):
        """
        Check Gemini API status and configuration.

        Returns information about whether the API is enabled and ready to use.
        """
        from django.conf import settings

        api_enabled = getattr(settings, 'GEMINI_REAL_API_ENABLED', False)

        return Response({
            'gemini_api_enabled': api_enabled,
            'status': 'ready' if api_enabled else 'disabled',
            'message': (
                'Gemini API is enabled and ready to accept queries.'
                if api_enabled else
                'Gemini API is currently disabled for safety. '
                'Set GEMINI_REAL_API_ENABLED=true to enable.'
            ),
            'documentation': 'README_GEMINI_SAFETY.md'
        })

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

        except RuntimeError as exc:
            # Check if this is the API disabled error
            error_message = str(exc)
            if 'Gemini API calls are disabled' in error_message:
                return Response(
                    {
                        'error': 'Gemini API is currently disabled',
                        'error_type': 'api_disabled',
                        'details': (
                            'Real Gemini API calls are disabled for safety. '
                            'To enable: Set GEMINI_REAL_API_ENABLED=true in environment variables '
                            'and restart the service.'
                        ),
                        'documentation': 'See README_GEMINI_SAFETY.md for details'
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            # Re-raise other RuntimeErrors
            raise

        except Exception as exc:
            # Check if this is a quota/rate limit error (429)
            error_message = str(exc)
            if '429' in error_message or 'RESOURCE_EXHAUSTED' in error_message:
                # Extract retry delay if available
                import re
                retry_match = re.search(r'retry in ([\d.]+)s', error_message)
                retry_after = int(float(retry_match.group(1))) if retry_match else 60

                return Response(
                    {
                        'error': 'API quota exceeded. Please try again later.',
                        'error_type': 'quota_exceeded',
                        'retry_after': retry_after,
                        'details': 'The Gemini API free tier quota has been reached. Please wait a few minutes and try again.'
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            # Other errors
            return Response(
                {
                    'error': f'Query failed: {str(exc)}',
                    'error_type': 'server_error',
                    'question': question,
                    'state': state
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
