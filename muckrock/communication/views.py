"""
Views for the communication app
"""

# Django
from django import http
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db.models import F, Q
from django.db.models.aggregates import Sum
from django.db.models.query import Prefetch
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic.detail import DetailView

# Third Party
from dal_select2.views import Select2ListView

# MuckRock
from muckrock.communication.filters import CheckFilterSet
from muckrock.communication.forms import CheckDateForm
from muckrock.communication.models import (
    Check,
    EmailAddress,
    EmailCommunication,
    EmailError,
    EmailOpen,
    FaxCommunication,
    FaxError,
    PhoneNumber,
)
from muckrock.communication.utils import get_email_or_fax
from muckrock.core.utils import new_action
from muckrock.core.views import (
    MRAutocompleteView,
    MRFilterListView,
    class_view_decorator,
)


class EmailDetailView(DetailView):
    """Show message open and error detail for an email address"""

    _prefetch_queryset = EmailCommunication.objects.select_related(
        "communication__foia__agency__jurisdiction", "from_email"
    ).prefetch_related(
        Prefetch("opens", queryset=EmailOpen.objects.select_related("recipient")),
        Prefetch("errors", queryset=EmailError.objects.select_related("recipient")),
        "to_emails",
        "cc_emails",
    )
    queryset = EmailAddress.objects.prefetch_related(
        Prefetch("from_emails", queryset=_prefetch_queryset),
        Prefetch("to_emails", queryset=_prefetch_queryset),
        Prefetch("cc_emails", queryset=_prefetch_queryset),
    )
    template_name = "communication/email_detail.html"
    pk_url_kwarg = "idx"
    context_object_name = "email_address"

    def get_context_data(self, **kwargs):
        """Add all email messages"""
        context = super(EmailDetailView, self).get_context_data(**kwargs)
        email_address = self.object
        context["emails"] = email_address.from_emails.union(
            email_address.to_emails.all(), email_address.cc_emails.all()
        ).order_by("sent_datetime")
        context["sidebar_admin_url"] = reverse(
            "admin:communication_emailaddress_change", args=(email_address.pk,)
        )
        return context


class PhoneDetailView(DetailView):
    """Show message error detail for a fax number"""

    _prefetch_queryset = FaxCommunication.objects.select_related(
        "communication__foia__agency__jurisdiction", "to_number"
    ).prefetch_related(
        Prefetch("errors", queryset=FaxError.objects.select_related("recipient"))
    )
    queryset = PhoneNumber.objects.prefetch_related(
        Prefetch("faxes", queryset=_prefetch_queryset)
    )
    template_name = "communication/fax_detail.html"
    pk_url_kwarg = "idx"
    context_object_name = "phone_number"

    def get_context_data(self, **kwargs):
        """Add all email messages"""
        context = super(PhoneDetailView, self).get_context_data(**kwargs)
        phone_number = self.object
        context["faxes"] = phone_number.faxes.order_by("sent_datetime")
        context["sidebar_admin_url"] = reverse(
            "admin:communication_phonenumber_change", args=(phone_number.pk,)
        )
        return context


@class_view_decorator(user_passes_test(lambda u: u.is_staff))
class CheckListView(MRFilterListView):
    """List of all checks we have issued"""

    model = Check
    title = "Checks"
    template_name = "communication/check_list.html"
    filter_class = CheckFilterSet
    queryset = Check.objects.select_related(
        "agency__jurisdiction", "communication__foia", "user"
    )

    def get_context_data(self, **kwargs):
        context = super(CheckListView, self).get_context_data(**kwargs)
        context["outstanding"] = Check.objects.filter(status="pending").aggregate(
            total=Sum("amount")
        )["total"]
        context["forms"] = {
            c.pk: CheckDateForm(instance=c, prefix=c.pk)
            for c in context["object_list"]
            if c.status == "pending"
        }
        return context

    def post(self, request, *args, **kwargs):
        """Handle updating checks deposit dates"""
        # pylint: disable=unused-argument
        for key in request.POST:
            if key.endswith("-status"):
                prefix = key.split("-", 1)[0]
                try:
                    check = Check.objects.get(pk=prefix)
                except (Check.DoesNotExist, ValueError):
                    messages.error(request, f"Error for {prefix}: Does not exist")
                else:
                    form = CheckDateForm(
                        data=request.POST, instance=check, prefix=prefix
                    )
                    if form.is_valid():
                        form.save()
                        foia = check.communication.foia
                        action = new_action(foia.agency, "check deposited", target=foia)
                        foia.notify(action)
                    else:
                        messages.error(
                            request, f"Error for {check.number}: {form.errors}"
                        )
        messages.success(request, "Check deposit dates updated")
        return redirect("check-list")


class CommunicationAutocomplete(MRAutocompleteView):
    """Base class for shared functionality between email and phone number autocompletes
    """

    def has_add_permission(self, request):
        """Staff only"""
        return request.user.is_staff

    def post(self, request, *args, **kwargs):
        """Create an object given a text after checking permissions.

        This is mostly the same as the parent class, but needs to be overriden
        to handle the case that the creation fails.
        """
        if not self.has_add_permission(request):
            return http.HttpResponseForbidden()

        if not self.create_field:
            raise ImproperlyConfigured('Missing "create_field"')

        text = request.POST.get("text", None)

        if text is None:
            return http.HttpResponseBadRequest()

        result = self.create_object(text)

        if result is None:
            return http.JsonResponse(
                {"id": -1, "text": self.create_error.format(text=text)}
            )

        return http.JsonResponse(
            {"id": result.pk, "text": self.get_result_label(result)}
        )


class EmailAutocomplete(CommunicationAutocomplete):
    """Autocomplete for emails"""

    queryset = EmailAddress.objects.filter(status="good").order_by("email")
    search_fields = ["email", "name"]
    create_field = "email"
    create_error = '"{text}" is not a valid email'

    def create_object(self, text):
        """Use email address fetch to create the object"""
        return EmailAddress.objects.fetch(text)


class PhoneNumberAutocomplete(CommunicationAutocomplete):
    """Autocomplete for phone numbers"""

    queryset = PhoneNumber.objects.order_by("number")
    search_fields = ["number"]
    create_field = "number"
    create_error = '"{text}" is not a valid phone/fax number'

    def get_queryset(self):
        """Pre process the query"""
        # pylint: disable=attribute-defined-outside-init

        # phone number is stored as ###-###-#### in the database
        # remove parens and convert spaces to dashes so that the user
        # can enter numbers in (###) ###-#### format as well
        self.q = self.q.translate({ord("("): None, ord(")"): None, ord(" "): "-"})
        return super().get_queryset()

    def get_result_label(self, result):
        """Show number type"""
        return f"{result.number} ({result.type})"

    def get_selected_result_label(self, result):
        """Show number type"""
        return self.get_result_label(result)

    def create_object(self, text):
        """Use phone number fetch to create the object"""
        types = {"(fax)": "fax", "(phone)": "phone"}

        # if they include a type, use it
        if " " in text:
            number, type_ = text.rsplit(" ", 1)
            if type_ in types:
                return PhoneNumber.objects.fetch(number, types[type_])

        # otherwise fall back to the default (fax)
        return PhoneNumber.objects.fetch(text)


class FaxAutocomplete(PhoneNumberAutocomplete):
    """Autocomplete for fax numbers"""

    queryset = PhoneNumber.objects.filter(status="good", type="fax").order_by("number")
    create_field = "number"
    create_error = '"{text}" is not a valid fax number'

    def create_object(self, text):
        """Use phone number fetch to create the object"""
        return PhoneNumber.objects.fetch(text)

    def get_result_label(self, result):
        """Do not show number type"""
        return str(result)


class EmailOrFaxAutocomplete(Select2ListView):
    """Autocomplete for an email or fax"""

    def autocomplete_results(self, results):
        """Get emails and faxes"""

        query = self.q
        emails = (
            EmailAddress.objects.filter(
                Q(email__icontains=query) | Q(name__icontains=query), status="good"
            )
            .order_by("email")
            .annotate(label=F("email"))
            .values("label")
        )

        phone_query = query.translate({ord("("): None, ord(")"): None, ord(" "): "-"})
        phones = (
            PhoneNumber.objects.filter(
                number__icontains=phone_query, type="fax", status="good"
            )
            .order_by("number")
            .annotate(label=F("number"))
            .values("label")
        )

        return list(emails.union(phones).values_list("label", flat=True)[:10])

    def create(self, text):
        """Create the email or fax from the given text"""
        try:
            return str(get_email_or_fax(text))
        except ValidationError:
            return None
