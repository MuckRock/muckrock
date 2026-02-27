"""
ViewSets for FOIA Coach API
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter

from apps.jurisdiction.models import ExampleResponse, JurisdictionResource, NFOICPartner
from apps.jurisdiction.services.muckrock_client import MuckRockAPIClient
from apps.jurisdiction.services.providers.helpers import (
    get_provider,
    list_available_providers,
    query_with_fallback
)
from .serializers import (
    ExampleResponseSerializer,
    JurisdictionSerializer,
    JurisdictionResourceSerializer,
    JurisdictionResourceUploadSerializer,
    NFOICPartnerSerializer,
    QueryRequestSerializer,
    QueryResponseSerializer,
)


class ExampleResponseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for ExampleResponse model.
    Read-only access to curated few-shot Q&A examples.
    """
    serializer_class = ExampleResponseSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['jurisdiction_abbrev', 'is_active']
    ordering_fields = ['order', 'created_at', 'title']
    ordering = ['order', 'title']

    def get_queryset(self):
        return ExampleResponse.objects.filter(is_active=True)


class NFOICPartnerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for NFOICPartner model.
    Read-only access to NFOIC state-level partner organizations.
    """
    serializer_class = NFOICPartnerSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['jurisdiction_abbrev', 'is_active']
    ordering_fields = ['order', 'name', 'jurisdiction_abbrev']
    ordering = ['jurisdiction_abbrev', 'order', 'name']

    def get_queryset(self):
        return NFOICPartner.objects.filter(is_active=True)


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

    @action(
        detail=False,
        methods=['post'],
        parser_classes=[MultiPartParser, FormParser],
        serializer_class=JurisdictionResourceUploadSerializer
    )
    def upload(self, request):
        """
        Upload a single PDF resource file.

        Accepts multipart/form-data with:
        - file: PDF file (required)
        - jurisdiction_abbrev: State abbreviation (required)
        - jurisdiction_id: Jurisdiction ID (required)
        - provider: Provider to upload to (optional, defaults to 'openai')
        - display_name: Display name (optional, auto-generated from filename)
        - description: Description (optional, generic default)
        - resource_type: Resource type (optional, defaults to 'general')

        Returns created resource with upload status.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Save creates the resource
        resource = serializer.save()

        # Initiate upload to specified provider (triggers signal)
        provider = request.data.get('provider', 'openai')
        resource.initiate_upload(provider)

        # Return resource with upload status
        response_serializer = JurisdictionResourceSerializer(resource)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )


class QueryViewSet(viewsets.ViewSet):
    """
    ViewSet for RAG query operations using Gemini File Search.
    """

    @action(detail=False, methods=['get'])
    def status(self, request):
        """
        Check RAG provider status and configuration.

        Returns information about available providers and their status.
        """
        from django.conf import settings

        available_providers = list_available_providers()
        current_provider = getattr(settings, 'RAG_PROVIDER', 'openai')

        # Check API enabled flags
        openai_enabled = getattr(settings, 'OPENAI_REAL_API_ENABLED', False)
        gemini_enabled = getattr(settings, 'GEMINI_REAL_API_ENABLED', False)

        return Response({
            'current_provider': current_provider,
            'available_providers': available_providers,
            'api_status': {
                'openai': 'enabled' if openai_enabled else 'disabled',
                'gemini': 'enabled' if gemini_enabled else 'disabled',
                'mock': 'always_enabled'
            },
            'status': 'ready',
            'message': f'Using {current_provider} provider. Set RAG_PROVIDER environment variable to change provider.',
            'documentation': 'See README for provider configuration details'
        })

    @action(detail=False, methods=['post'])
    def query(self, request):
        """
        Execute a RAG query against jurisdiction resources.

        Request body:
        {
            "question": "What is the response time in Colorado?",
            "state": "CO",  # optional
            "provider": "openai",  # optional, defaults to RAG_PROVIDER setting
            "context": {},  # optional additional context
            "model": "gpt-4o"  # optional model selection
        }
        """
        serializer = QueryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question = serializer.validated_data['question']
        state = serializer.validated_data.get('state')
        provider_name = serializer.validated_data.get('provider')
        context = serializer.validated_data.get('context')
        model = serializer.validated_data.get('model')
        system_prompt = serializer.validated_data.get('system_prompt')

        try:
            # Use query_with_fallback for automatic provider fallback
            result = query_with_fallback(
                question=question,
                state=state,
                provider_name=provider_name,
                context=context,
                model=model,
                system_prompt=system_prompt
            )

            response_serializer = QueryResponseSerializer(result)
            return Response(response_serializer.data)

        except RuntimeError as exc:
            # Check if this is the API disabled error
            error_message = str(exc)
            if 'API calls are disabled' in error_message:
                return Response(
                    {
                        'error': f'{provider_name} API is currently disabled',
                        'error_type': 'api_disabled',
                        'details': (
                            f'Real {provider_name} API calls are disabled for safety. '
                            f'To enable: Set {provider_name.upper()}_REAL_API_ENABLED=true in environment variables '
                            'and restart the service.'
                        ),
                        'documentation': 'See README for provider configuration details'
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
                        'details': 'The API free tier quota has been reached. Please wait a few minutes and try again.'
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )

            # Other errors
            return Response(
                {
                    'error': f'Query failed: {str(exc)}',
                    'error_type': 'server_error',
                    'question': question,
                    'state': state,
                    'provider': provider_name
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
