"""Views for the gethelp app"""

# Django
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST

# MuckRock
from muckrock.gethelp.tasks import create_gethelp_ticket


@require_POST
def contact(request):
    """Queue a Zendesk support ticket from the Get Help form."""
    text = request.POST.get("text", "").strip()
    if not text:
        return JsonResponse({"message": "Please describe your issue."}, status=400)

    user_pk = request.user.pk if request.user.is_authenticated else None
    foia_pk = request.POST.get("foia_pk") or None
    category_label = request.POST.get("category_label", "")
    problem_title = request.POST.get("problem_title", "")

    if settings.USE_ZENDESK:
        create_gethelp_ticket.delay(
            user_pk=user_pk,
            text=text,
            foia_pk=foia_pk,
            category_label=category_label,
            problem_title=problem_title,
        )

    return JsonResponse(
        {"message": "Your message has been sent. We'll be in touch soon."}
    )
