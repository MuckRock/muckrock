"""Rules based permissions for the agency app"""

# needed for rules

# Third Party
from rules import add_perm

# MuckRock
from muckrock.foia.rules import has_feature_level

add_perm('agency.view_emails', has_feature_level(1))
