"""
Utility functions for agencies
"""

# Django
from django.template.loader import get_template
from django.utils.encoding import smart_text


def initial_communication_template(
    agencies, user_name, requested_docs, **kwargs
):
    """Construct the initial communication template language for a given set
    of agencies
    """

    jurisdictions = set(a.jurisdiction.legal for a in agencies)
    if len(jurisdictions) == 1:
        jurisdiction = jurisdictions.pop()
    elif kwargs.get('html'):
        jurisdiction = {
            'get_law_name':
                '<abbr title="This will be replaced by the relevant '
                'transparency law">{ law name }</abbr>',
            'days':
                '<abbr title="This will be replaced by the number of days '
                'the law permits before a response is required">{ number of days }'
                '</abbr>',
            'get_day_type':
                '<abbr title="This will be replaced by business or '
                'calendar, depending on whether the law counts weekends and other '
                'holidays in its deadline">{ business or calendar }</abbr>',
        }
    else:
        jurisdiction = {
            'get_law_name': '{ law name }',
            'days': '{ number of days }',
            'get_day_type': '{ business or calendar }',
        }
    requested_docs = requested_docs.replace('{ name }', user_name)
    if len(jurisdictions) == 1 and kwargs.get('edited_boilerplate'):
        tags = [
            ('{ law name }', jurisdiction.get_law_name()),
            ('{ short name }', jurisdiction.get_law_name(abbrev=True)),
            ('{ number of days }', jurisdiction.days or 10),
            ('{ business or calendar }', jurisdiction.get_day_type()),
        ]
        for tag, replace in tags:
            requested_docs = requested_docs.replace(tag, unicode(replace))
        return requested_docs
    if not kwargs.get('edited_boilerplate'):
        template = get_template('text/foia/request.txt')
        context = {
            'requested_docs': smart_text(requested_docs),
            'jurisdiction': jurisdiction,
            'user_name': user_name,
            'proxy': kwargs.get('proxy'),
        }
        return template.render(context)
