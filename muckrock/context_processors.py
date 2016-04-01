"""
Site-wide context processors
"""

def google_analytics(request):
    """
    Retrieve and delete any google analytics session data and send it to the template
    """
    return {'ga': request.session.pop('ga', None)}
