"""Constants for the organization app"""
# MuckRock
from muckrock.organization.choices import Plan

# XXX put plans into database

# beta plan, staff plan, custom plans

MIN_USERS = {Plan.free: 1, Plan.pro: 1, Plan.basic: 5, Plan.plus: 5}

BASE_REQUESTS = {Plan.free: 0, Plan.pro: 20, Plan.basic: 50, Plan.plus: 100}

EXTRA_REQUESTS_PER_USER = {
    Plan.free: 0,
    Plan.pro: 0,
    Plan.basic: 5,
    Plan.plus: 10,
}
