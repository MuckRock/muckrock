"""
Custom object managers
"""

# Django
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

# Third Party
from actstream.managers import ActionManager, stream


class MRActionManager(ActionManager):
    """Adds custom activity streams"""

    @stream
    def owned_by(self, user, model, **kwargs):
        """Get the stream for all requests with the given owner"""
        if user is None or not isinstance(user, User):
            raise ValueError('Must provide a User')
        ctype = ContentType.objects.get_for_model(model)
        if model.__name__ == 'FOIARequest':
            user_filter = {'composer__user': user}
        else:
            user_filter = {'user': user}
        pks = list(
            model.objects.filter(**user_filter).values_list('pk', flat=True)
        )
        if not pks:
            # self.none is inherited from the GFKManager parent
            return self.none()
        else:
            return self.public((
                Q(
                    actor_content_type=ctype,
                    actor_object_id__in=pks,
                ) | Q(
                    target_content_type=ctype,
                    target_object_id__in=pks,
                ) | Q(
                    action_object_content_type=ctype,
                    action_object_object_id__in=pks,
                )
            ), **kwargs)
