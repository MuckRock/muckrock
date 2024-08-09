"""
Viewsets for V2 of the FOIA API
"""

# Third Party
from rest_framework import mixins, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

# MuckRock
from muckrock.foia.api_v2.serializers import FOIARequestSerializer
from muckrock.foia.models.request import FOIARequest


class FOIARequestViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """API for FOIA Requests"""

    authentication_classes = [JWTAuthentication, SessionAuthentication]
    serializer_class = FOIARequestSerializer
    filter_backends = ()

    def get_queryset(self):
        return (
            FOIARequest.objects.get_viewable(self.request.user)
            .select_related("composer")
            .prefetch_related(
                "edit_collaborators", "read_collaborators", "tracking_ids"
            )
        )
