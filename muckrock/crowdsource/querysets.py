"""Querysets for the Crowdsource application"""

# Django
from django.db import models
from django.db.models import Case, Count, Q, Sum, Value, When


class CrowdsourceQuerySet(models.QuerySet):
    """Object manager for crowdsources"""

    def get_viewable(self, user):
        """Get the viewable crowdsources for the user"""
        if user.is_staff:
            return self
        elif user.is_authenticated:
            return self.filter(
                Q(user=user)
                | Q(status="open", project_only=False)
                | Q(status="open", project_only=True, project__contributors=user)
            )
        else:
            return self.filter(status="open", project_only=False)


class CrowdsourceDataQuerySet(models.QuerySet):
    """Object manager for crowdsource data"""

    def get_choices(self, data_limit, user, ip_address):
        """Get choices for data to show"""
        choices = self.annotate(
            count=Sum(
                Case(
                    When(responses__number=1, then=Value(1)),
                    default=0,
                    output_field=models.IntegerField(),
                )
            )
        ).filter(count__lt=data_limit)
        if user is not None:
            choices = choices.exclude(responses__user=user)
        elif ip_address is not None:
            choices = choices.exclude(responses__ip_address=ip_address)
        return choices


class CrowdsourceResponseQuerySet(models.QuerySet):
    """Object manager for crowdsource responses"""

    def get_user_count(self):
        """Get the number of distinct users who have responded"""
        return self.aggregate(Count("user", distinct=True))["user__count"]
