from os import environ

CONSTANCE_REDIS_CONNECTION = {
    'host': environ.get("REDIS_HOST"),
    'port': 6379,
}

# Forwarding settings for these addresses should be set in Mailgun settings
DEFAULT_FROM_EMAIL = "info@foi-requests.washpost.com"
DIAGNOSTIC_EMAIL = "diagnostics@foi-requests.washpost.com"
SCANS_EMAIL = "scans@foi-requests.washpost.com"
ASSIGNMENTS_EMAIL = "assignments@foi-requests.washpost.com"

ADDRESS_NAME = "The Washington Post"
ADDRESS_DEPT = "DEPT FOI {pk}"
ADDRESS_STREET = "1301 K St. NW"
ADDRESS_CITY = "Washington"
ADDRESS_STATE = "DC"
ADDRESS_ZIP = "20005"

PHONE_NUMBER = "(202) 334-6000"
PHONE_NUMBER_LINK = PHONE_NUMBER.translate({ord(i): None for i in "()- "})
