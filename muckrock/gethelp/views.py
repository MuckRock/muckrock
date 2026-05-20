"""Views for the gethelp app"""

# Django
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST

# MuckRock
from muckrock.gethelp.forms import GetHelpForm
from muckrock.gethelp.tasks import create_gethelp_ticket


@require_POST
def contact(request):
    """Queue a Zendesk support ticket from the Get Help form."""
    form = GetHelpForm(request.POST)
    if not form.is_valid():
        first_error = next(iter(form.errors.values()))[0]
        return JsonResponse({"message": first_error}, status=400)

    user_pk = request.user.pk if request.user.is_authenticated else None

    if settings.USE_ZENDESK:
        create_gethelp_ticket.delay(
            user_pk=user_pk,
            text=form.cleaned_data["text"],
            foia_pk=form.cleaned_data["foia_pk"],
            category_label=form.cleaned_data["category_label"],
            problem_title=form.cleaned_data["problem_title"],
        )

    return JsonResponse(
        {"message": "Your message has been sent. We'll be in touch soon."}
    )
