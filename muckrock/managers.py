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
    def owned_by(self, user, model, **kwargs):
        """Get the stream for all requests with the given owner"""
        if user is None or not isinstance(user, User):
            raise ValueError('Must provide a User')
        # TODO: check that the model is registered with activity streams
        ctype = ContentType.objects.get_for_model(model)
        pks = list(model.objects.filter(user=user).values_list('pk', flat=True))
        if not pks:
            # self.none is inherited from the GFKManager parent
            return self.none()
        else:
            return self.public(
                (Q(
                    actor_content_type=ctype,
                    actor_object_id__in=pks,
                ) | Q(
                    target_content_type=ctype,
                    target_object_id__in=pks,
                ) | Q(
                    action_object_content_type=ctype,
                    action_object_object_id__in=pks,
                )), **kwargs)
