"""
Constants for the FOIA app
"""

# Standard Library
import os

# submit a composer with a 35 minute delay
COMPOSER_SUBMIT_DELAY = 35 * 60

# allow a composer to be edited 30 minutes after it has been submitted
COMPOSER_EDIT_DELAY = 30 * 60

FOIA_CSV_CHUNK_SIZE = int(os.environ.get('FOIA_CSV_CHUNK_SIZE', 1000))
