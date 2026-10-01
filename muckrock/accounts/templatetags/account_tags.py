"""
Template tags for the accounts application
"""

# Django
from django import template

# MuckRock
from muckrock.accounts.forms import InternalNoteForm
from muckrock.accounts.utils import can_see_internal_notes, note_form_prefix

register = template.Library()


@register.inclusion_tag("accounts/internal_notes.html", takes_context=True)
def internal_notes(context, user_obj):
    """Show and edit the private staff notes about a user

    Renders nothing at all for anybody who may not see internal notes.
    """
    request = context.get("request")
    if request is None or user_obj is None:
        return {"show_notes": False}
    if not can_see_internal_notes(request.user):
        return {"show_notes": False}

    notes = [
        {
            "note": note,
            "form": InternalNoteForm(instance=note, prefix=note_form_prefix(note=note)),
        }
        for note in user_obj.internal_notes.select_related("by__profile", "category")
    ]
    return {
        "show_notes": True,
        # the inclusion tag gets a fresh context, so pass along what the
        # forms in the template need
        "csrf_token": context.get("csrf_token"),
        "notes_user": user_obj,
        "notes": notes,
        "note_form": InternalNoteForm(prefix=note_form_prefix(user=user_obj)),
        "next": request.get_full_path(),
    }
