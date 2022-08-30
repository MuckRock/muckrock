"""Rules based permissions for the Q&A app"""
# Third Party
from rules import add_perm

# MuckRock
from muckrock.foia.rules import is_staff

add_perm("qanda.block", is_staff)
