"""
All models for agency application
"""

# MuckRock
from muckrock.agency.models.agency import Agency, AgencyType
from muckrock.agency.models.communication import (
    AgencyAddress,
    AgencyEmail,
    AgencyPhone,
)
from muckrock.agency.models.request_form import (
    AgencyRequestForm,
    AgencyRequestFormMapper,
)
