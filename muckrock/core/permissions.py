# Third Party
from rest_framework import permissions


class DjangoObjectPermissionsOrAnonReadOnly(permissions.DjangoObjectPermissions):
    """Use Django Object permissions as the base for our permissions
    Allow anonymous read-only access
    """

    authenticated_users_only = False
