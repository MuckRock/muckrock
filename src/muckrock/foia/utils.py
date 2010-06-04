"""Utility functions for the FOIA Application"""

def make_template_choices(template_dict):
    """Make the data structure for the select form from the more generic data strcuture"""
    categories = set(t.category for t in template_dict.values())

    choices = []

    for category in categories:
        if category is not None:
            templates = [t for t in template_dict.values() if t.category == category]
            choices.append((category, [(t.id, t.name) for t in templates]))

    for template in [t for t in template_dict.values() if t.category is None]:
        choices.append((template.id, template.name))

    return choices
