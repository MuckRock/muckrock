"""
Utility functions for agencies
"""

# Django
from django.template.loader import get_template
from django.utils.encoding import smart_text


def initial_communication_template(agencies, user_name, requested_docs, **kwargs):
    """Construct the initial communication template language for a given set
    of agencies
    """

    jurisdictions = set(a.jurisdiction.legal for a in agencies)
    jurisdictions = jurisdictions.union(
        j.legal for j in kwargs.get("extra_jurisdictions", [])
    )
    num_jurisdictions = len(jurisdictions)
    if num_jurisdictions == 1:
        jurisdiction = jurisdictions.pop()
    elif kwargs.get("html"):
        jurisdiction = {
            "get_law_name": '<abbr class="tooltip" title="This will be replaced by the '
            'relevant transparency law">{ law name }</abbr>',
            "get_days": '<abbr class="tooltip" title="Number of days statute requires, '
            'or default of 10 days if no requirement">{ days }</abbr>',
        }
    else:
        jurisdiction = {"get_law_name": "{ law name }", "get_days": "{ days }"}
    requested_docs = requested_docs.replace("{ name }", user_name)

    if num_jurisdictions == 1 and kwargs.get("edited_boilerplate"):
        tags = [
            ("{ law name }", jurisdiction.get_law_name()),
            ("{ short name }", jurisdiction.get_law_name(abbrev=True)),
            ("{ days }", jurisdiction.get_days()),
            # old tags
            ("{ number of days }", jurisdiction.days or 10),
            ("{ business or calendar }", jurisdiction.get_day_type()),
        ]
        if len(agencies) == 1:
            tags.append(("{ agency name }", agencies[0].name))
        for tag, replace in tags:
            requested_docs = requested_docs.replace(tag, str(replace))
        return requested_docs
    elif kwargs.get("edited_boilerplate"):
        return requested_docs
    else:
        template = get_template("text/foia/request.txt")
        context = {
            "requested_docs": smart_text(requested_docs),
            "jurisdiction": jurisdiction,
            "user_name": user_name,
            "proxy": kwargs["proxy"].profile.full_name if "proxy" in kwargs else None,
        }
        return template.render(context)
