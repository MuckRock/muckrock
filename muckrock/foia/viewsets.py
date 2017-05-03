"""
Viewsets for the FOIA API
"""

from django.conf import settings
from django.core.files.base import ContentFile
from django.template.defaultfilters import slugify
from django.template.loader import get_template
from django.template import RequestContext

import actstream
from datetime import datetime
from rest_framework import decorators, status as http_status, viewsets
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework.response import Response
import django_filters
import logging
import requests

from muckrock.agency.models import Agency
from muckrock.foia.models import FOIARequest, FOIACommunication, FOIAFile
from muckrock.foia.serializers import (
        FOIARequestSerializer,
        FOIACommunicationSerializer,
        FOIAPermissions,
        IsOwner,
        )
from muckrock.jurisdiction.models import Jurisdiction

# pylint: disable=too-many-ancestors
# pylint: disable=bad-continuation

logger = logging.getLogger(__name__)


class MimeError(Exception):
    """Try to attach a file with a disallowed mime type"""

class FOIARequestViewSet(viewsets.ModelViewSet):
    """
    API views for FOIARequest

    Filter fields:
    * title
    * embargo
    * user, by username
    * jurisdiction, by id
    * agency, by id
    * tags, by name
    """
    # pylint: disable=too-many-public-methods
    serializer_class = FOIARequestSerializer
    permission_classes = (FOIAPermissions,)

    class Filter(django_filters.FilterSet):
        """API Filter for FOIA Requests"""
        # pylint: disable=too-few-public-methods
        agency = django_filters.NumberFilter(name='agency__id')
        jurisdiction = django_filters.NumberFilter(name='jurisdiction__id')
        user = django_filters.CharFilter(name='user__username')
        tags = django_filters.CharFilter(name='tags__name')

        class Meta:
            model = FOIARequest
            fields = ('user', 'title', 'status', 'embargo', 'jurisdiction', 'agency', 'tags')

    filter_class = Filter

    def get_queryset(self):
        return (FOIARequest.objects.get_viewable(self.request.user)
            .select_related(
                'user',
                'agency',
                'jurisdiction'
            )
            .prefetch_related(
                'communications__files',
                'notes',
                'tags',
                'edit_collaborators',
                'read_collaborators'
            )
        )

    def create(self, request):
        """Submit new request"""
        # pylint: disable=too-many-locals
        data = request.data
        try:
            jurisdiction = Jurisdiction.objects.get(pk=int(data['jurisdiction']))
            agency = Agency.objects.get(pk=int(data['agency']), jurisdiction=jurisdiction)

            requested_docs = data['document_request']
            template = get_template('text/foia/request.txt')
            context = RequestContext(request, {
                'document_request': requested_docs,
                'jurisdiction': jurisdiction,
                'user_name': request.user.get_full_name,
                })
            text = template.render(context)
            title = data['title']

            slug = slugify(title) or 'untitled'
            foia = FOIARequest.objects.create(
                    user=request.user,
                    status='started',
                    title=title,
                    jurisdiction=jurisdiction,
                    slug=slug,
                    agency=agency,
                    requested_docs=requested_docs,
                    description=requested_docs,
                    )

            comm = FOIACommunication.objects.create(
                    foia=foia,
                    communication=text,
                    from_who=request.user.get_full_name(),
                    to_who=foia.get_to_who(),
                    date=datetime.now(),
                    response=False,
                    )

            if 'attachments' in data:
                attachments = data.get('attachments')[:3]
            else:
                attachments = []
            for attm_path in attachments:
                res = requests.get(attm_path)
                mime_type = res.header['Conent-Type']
                if mime_type not in settings.ALLOWED_FILE_MIMES:
                    raise MimeError
                res.raise_for_status()
                title = attm_path.rsplit('/', 1)[1]
                file_ = FOIAFile.objects.create(
                        access='public',
                        foia=foia,
                        comm=comm,
                        title=title,
                        date=datetime.now(),
                        source=request.user.get_full_name(),
                        )
                file_.ffile.save(title, ContentFile(res.content))

            if request.user.profile.make_request():
                foia.submit()
                return Response({'status': 'FOI Request submitted',
                                 'Location': foia.get_absolute_url()},
                                 status=http_status.HTTP_201_CREATED)
            else:
                return Response(
                    {'status':
                        'Error - Out of requests.  FOI Request has been saved.',
                     'Location': foia.get_absolute_url()},
                    status=http_status.HTTP_402_PAYMENT_REQUIRED)

        except KeyError:
            return Response(
                {'status':
                    'Missing data - Please supply title, document_request, '
                    'jurisdiction, and agency'},
                status=http_status.HTTP_400_BAD_REQUEST)
        except (Jurisdiction.DoesNotExist, Agency.DoesNotExist):
            return Response(
                {'status':
                    'Bad data - please supply jurisdiction and agency as the PK'
                    ' of existing entities.  Agency must be in Jurisdiction.'},
                status=http_status.HTTP_400_BAD_REQUEST)
        except (requests.exceptions.RequestException, TypeError, MimeError):
            # TypeError is thrown if 'attachments' is not a list
            return Response(
                {'status':
                    'There was a problem with one of your attachments'},
                status=http_status.HTTP_400_BAD_REQUEST)

    @decorators.detail_route(permission_classes=(IsOwner,))
    def followup(self, request, pk=None):
        """Followup on a request"""
        try:
            foia = FOIARequest.objects.get(pk=pk)
            self.check_object_permissions(request, foia)

            foia.create_out_communication(
                    from_user=request.user,
                    text=request.DATA['text'],
                    )

            can_appeal = request.user.has_perm('foia.appeal_foiarequest', foia)
            appeal = request.DATA.get('appeal', False) and can_appeal
            foia.submit(appeal=appeal)

            if appeal:
                status = 'Appeal submitted'
            else:
                status = 'Follow up submitted'

            return Response({'status': status},
                             status=http_status.HTTP_200_OK)

        except FOIARequest.DoesNotExist:
            return Response({'status': 'Not Found'}, status=http_status.HTTP_404_NOT_FOUND)

        except KeyError:
            return Response({'status': 'Missing data - Please supply text for followup'},
                             status=http_status.HTTP_400_BAD_REQUEST)

    @decorators.detail_route(methods=['POST', 'DELETE'], permission_classes=(IsAuthenticated,))
    def follow(self, request, pk=None):
        """Follow or unfollow a request"""

        try:
            foia = FOIARequest.objects.get(pk=pk)
            self.check_object_permissions(request, foia)

            if foia.user == request.user:
                return Response({'status': 'You may not follow your own request'},
                                status=http_status.HTTP_400_BAD_REQUEST)

            if request.method == 'POST':
                actstream.actions.follow(request.user, foia, actor_only=False)
                return Response({'status': 'Following'}, status=http_status.HTTP_200_OK)
            if request.method == 'DELETE':
                actstream.actions.unfollow(request.user, foia)
                return Response({'status': 'Not following'}, status=http_status.HTTP_200_OK)

        except FOIARequest.DoesNotExist:
            return Response({'status': 'Not Found'}, status=http_status.HTTP_404_NOT_FOUND)

    def post_save(self, obj, created=False):
        """Save tags"""
        if 'tags' in self.request.DATA:
            obj.tags.set(*self.request.DATA['tags'])
        return super(FOIARequestViewSet, self).post_save(obj, created=created)


class FOIACommunicationViewSet(viewsets.ModelViewSet):
    """API views for FOIARequest"""
    # pylint: disable=too-many-public-methods
    queryset = FOIACommunication.objects.prefetch_related('files')
    serializer_class = FOIACommunicationSerializer
    permission_classes = (DjangoModelPermissions,)

    class Filter(django_filters.FilterSet):
        """API Filter for FOIA Communications"""
        # pylint: disable=too-few-public-methods
        min_date = django_filters.DateFilter(name='date', lookup_type='gte')
        max_date = django_filters.DateFilter(name='date', lookup_type='lte')
        class Meta:
            model = FOIACommunication
            fields = ('max_date', 'min_date', 'foia', 'status', 'response', 'delivered')

    filter_class = Filter
