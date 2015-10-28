"""
Custom object managers
"""

from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from actstream.managers import ActionManager, stream

from muckrock.foia.models import FOIARequest

class MRActionManager(ActionManager):
    """Adds custom activity streams"""

    @stream
    def requests_for_user(self, user, **kwargs):
        """Get the stream for all requests with the given owner"""
        if user is None or not isinstance(user, User):
            raise ValueError('Must provide a User')
        foias = FOIARequest.objects.filter(user=user)
        if not foias.exists():
            # self.none is inherited from the GFKManager parent
            return self.none()
        foia_pks = [foia.pk for foia in foias]
        ctype = ContentType.objects.get_for_model(foias.first())
        return self.public(
            Q(
                actor_content_type=ctype,
                actor_object_id__in=foia_pks,
            ) | Q(
                target_content_type=ctype,
                target_object_id__in=foia_pks,
            ) | Q(
                action_object_content_type=ctype,
                action_object_object_id__in=foia_pks,
            ), **kwargs)
