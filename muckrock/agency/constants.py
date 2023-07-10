"""
Constants for the agency app
"""

# Standard Library
import os

STALE_REPLIES = int(os.environ.get("STALE_REPLIES", 150))
FOIA_FILE_LIMIT = 25
FOIA_LOG_LIMIT = 25
