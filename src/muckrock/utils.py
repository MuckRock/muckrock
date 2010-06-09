"""Utility functions"""

def try_or_none(exception, callable_, *args, **kwargs):
    """Return result of callable called with args, or none if exception is thrown"""
    try:
        return callable_(*args, **kwargs)
    except exception:
        return None

def process_get(query_dict):
    """Process a GET QueryDict into a regular dict suitable for a form"""
    param_dict = {}
    for key, val in query_dict.iteritems():
        param_dict[key] = val

    return param_dict
