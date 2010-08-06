"""Utility functions"""

def try_or_none(exception, callable_, *args, **kwargs):
    """Return result of callable called with args, or none if exception is thrown"""
    try:
        return callable_(*args, **kwargs)
    except exception:
        return None
