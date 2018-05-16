"""
Constants for the agency app
"""

# Standard Library
import os

STALE_REPLIES = int(os.environ.get('STALE_REPLIES', 150))
