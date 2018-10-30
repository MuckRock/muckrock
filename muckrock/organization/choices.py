"""
Field choices for the organization app
"""

# Third Party
from djchoices import ChoiceItem, DjangoChoices


class Plan(DjangoChoices):
    """The plan choices available for organizations
    These choices are replicated across all sites,
    be sure to keep them in sync
    """

    free = ChoiceItem(0)
    pro = ChoiceItem(1)
    basic = ChoiceItem(2)
    plus = ChoiceItem(3)
