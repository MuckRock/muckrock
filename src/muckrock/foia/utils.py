"""Utility functions for the FOIA Application"""

def make_template_choices(template_dict, level):
    """Make the data structure for the select form from the more generic data strcuture"""
    templates = [t for t in template_dict.values() if t.level == level or t.level == 'both']
    categories = set(t.category for t in templates)

    choices = []

    for category in categories:
        if category is not None:
            cat_templates = [t for t in templates if t.category == category]
            choices.append((category, [(t.id, t.name) for t in cat_templates]))

    for template in [t for t in templates if t.category is None]:
        choices.append((template.id, template.name))

    return choices
