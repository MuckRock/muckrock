# -*- coding: utf-8 -*-
"""Views for the crowdsource app"""

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.db.models import Count
from django.db.models.query import Prefetch
from django.http import Http404, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    TemplateView,
    UpdateView,
)
from django.views.generic.detail import BaseDetailView

# Standard Library
from itertools import zip_longest

# Third Party
import requests
from ipware import get_client_ip

# MuckRock
from muckrock.accounts.mixins import MiniregMixin
from muckrock.accounts.utils import mixpanel_event
from muckrock.core.views import (
    MRAutocompleteView,
    MRFilterListView,
    class_view_decorator,
)
from muckrock.crowdsource.filters import CrowdsourceFilterSet
from muckrock.crowdsource.forms import (
    CrowdsourceAssignmentForm,
    CrowdsourceDataCsvForm,
    CrowdsourceDataFormset,
    CrowdsourceForm,
    CrowdsourceMessageResponseForm,
)
from muckrock.crowdsource.models import (
    Crowdsource,
    CrowdsourceData,
    CrowdsourceField,
    CrowdsourceResponse,
    CrowdsourceValue,
)
from muckrock.crowdsource.tasks import export_csv
from muckrock.message.email import TemplateEmail


class CrowdsourceExploreView(TemplateView):
    """Provides a space for exploring active assignments"""

    template_name = "crowdsource/explore.html"

    def get_context_data(self, **kwargs):
        """Data for the explore page"""
        context = super(CrowdsourceExploreView, self).get_context_data(**kwargs)
        context["crowdsource_users"] = CrowdsourceResponse.objects.get_user_count()
        context["crowdsource_data"] = CrowdsourceResponse.objects.count()
        context["crowdsource_count"] = Crowdsource.objects.exclude(
            status="draft"
        ).count()
        context["crowdsources"] = (
            Crowdsource.objects.annotate(
                user_count=Count("responses__user", distinct=True)
            )
            .order_by("-datetime_created")
            .filter(status="open", project_only=False, featured=True)
            .select_related("user", "project")
            .prefetch_related(
                "data",
                Prefetch(
                    "responses",
                    queryset=CrowdsourceResponse.objects.select_related(
                        "user__profile"
                    ),
                ),
            )[:5]
        )
        return context


class CrowdsourceDetailView(DetailView):
    """A view for those with permission to view the particular crowdsource"""

    template_name = "crowdsource/detail.html"
    pk_url_kwarg = "idx"
    query_pk_and_slug = True
    context_object_name = "crowdsource"
    queryset = Crowdsource.objects.select_related("user").prefetch_related(
        "data", "responses"
    )

    def dispatch(self, *args, **kwargs):
        """Redirect to assignment page for those without permission"""
        crowdsource = self.get_object()
        if not self.request.user.has_perm("crowdsource.view_crowdsource", crowdsource):
            return redirect(
                "crowdsource-assignment", slug=crowdsource.slug, idx=crowdsource.pk
            )
        return super(CrowdsourceDetailView, self).dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        """Handle CSV downloads"""
        crowdsource = self.get_object()
        has_perm = self.request.user.has_perm(
            "crowdsource.change_crowdsource", crowdsource
        )
        if self.request.GET.get("csv") and has_perm:
            export_csv.delay(crowdsource.pk, self.request.user.pk)
            messages.info(
                self.request,
                "Your CSV is being processed.  It will be emailed to you when "
                "it is ready.",
            )
        return super(CrowdsourceDetailView, self).get(request, *args, **kwargs)

    def post(self, request, *_args, **_kwargs):
        """Handle actions on the crowdsource"""
        crowdsource = self.get_object()
        has_perm = self.request.user.has_perm(
            "crowdsource.change_crowdsource", crowdsource
        )
        if not has_perm:
            messages.error(
                request, "You do not have permission to edit this assignment"
            )
            return redirect(crowdsource)
        if request.POST.get("action") == "Close":
            crowdsource.status = "close"
            crowdsource.save()
            messages.success(request, "The assignment has been closed")
        elif request.POST.get("action") == "Add Data":
            form = CrowdsourceDataCsvForm(request.POST, request.FILES)
            if form.is_valid():
                form.process_data_csv(crowdsource)
                messages.success(request, "The data is being added to the assignment")
            else:
                messages.error(request, form.errors)
        return redirect(crowdsource)

    def get_context_data(self, **kwargs):
        """Admin link"""
        context = super(CrowdsourceDetailView, self).get_context_data(**kwargs)
        context["sidebar_admin_url"] = reverse(
            "admin:crowdsource_crowdsource_change", args=(self.object.pk,)
        )
        context["message_form"] = CrowdsourceMessageResponseForm()
        context["data_form"] = CrowdsourceDataCsvForm()
        context["edit_access"] = self.request.user.has_perm(
            "crowdsource.change_crowdsource", self.object
        )
        return context


class CrowdsourceFormView(MiniregMixin, BaseDetailView, FormView):
    """A view for a user to fill out the crowdsource form"""

    template_name = "crowdsource/form.html"
    form_class = CrowdsourceAssignmentForm
    pk_url_kwarg = "idx"
    query_pk_and_slug = True
    context_object_name = "crowdsource"
    queryset = Crowdsource.objects.filter(status__in=["draft", "open"])
    minireg_source = "Crowdsource"
    field_map = {"email": "email", "name": "full_name"}

    def dispatch(self, request, *args, **kwargs):
        """Check permissions"""
        # pylint: disable=attribute-defined-outside-init
        self.object = self.get_object()
        edit_perm = request.user.has_perm("crowdsource.change_crowdsource", self.object)
        form_perm = request.user.has_perm("crowdsource.form_crowdsource", self.object)
        if self.object.status == "draft" and not edit_perm:
            raise Http404
        if not form_perm:
            messages.error(request, "That crowdsource is private")
            return redirect("crowdsource-list")
        return super(CrowdsourceFormView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Cache the object for POST requests"""
        # pylint: disable=attribute-defined-outside-init
        crowdsource = self.get_object()
        data_id = self.request.POST.get("data_id")
        if data_id:
            self.data = crowdsource.data.filter(pk=data_id).first()
        else:
            self.data = None

        if crowdsource.status == "draft":
            messages.error(request, "No submitting to draft crowdsources")
            return redirect(crowdsource)
        if request.POST.get("submit") == "Skip":
            return self.skip()
        return super(CrowdsourceFormView, self).post(request, args, kwargs)

    def get(self, request, *args, **kwargs):
        """Check if there is a valid assignment"""
        ip_address, _ = get_client_ip(self.request)
        has_assignment = self._has_assignment(
            self.get_object(), self.request.user, ip_address
        )
        if has_assignment:
            return super(CrowdsourceFormView, self).get(request, args, kwargs)
        else:
            messages.warning(
                request,
                "Sorry, there are no assignments left for you to complete "
                "at this time for that crowdsource",
            )
            return redirect("crowdsource-list")

    def _has_assignment(self, crowdsource, user, ip_address):
        """Check if the user has a valid assignment to complete"""
        # pylint: disable=attribute-defined-outside-init
        if user.is_anonymous:
            user = None
        else:
            ip_address = None
        self.data = crowdsource.get_data_to_show(user, ip_address)
        if crowdsource.data.exists():
            return self.data is not None
        else:
            return not (
                crowdsource.user_limit
                and crowdsource.responses.filter(
                    user=user, ip_address=ip_address
                ).exists()
            )

    def get_form_kwargs(self):
        """Add the crowdsource object to the form"""
        kwargs = super(CrowdsourceFormView, self).get_form_kwargs()
        kwargs.update(
            {
                "crowdsource": self.get_object(),
                "user": self.request.user,
                "datum": self.data,
            }
        )
        return kwargs

    def get_context_data(self, **kwargs):
        """Get the data source to show, if there is one"""
        if "data" not in kwargs:
            kwargs["data"] = self.data
        if self.object.multiple_per_page and self.request.user.is_authenticated:
            kwargs["number"] = (
                self.object.responses.filter(
                    user=self.request.user, data=kwargs["data"]
                ).count()
                + 1
            )
        else:
            kwargs["number"] = 1
        return super(CrowdsourceFormView, self).get_context_data(**kwargs)

    def get_initial(self):
        """Fetch the crowdsource data item to show with this form,
        if there is one"""
        if self.request.method == "GET" and self.data is not None:
            return {"data_id": self.data.pk}
        else:
            return {}

    def form_valid(self, form):
        """Save the form results"""
        crowdsource = self.get_object()
        has_data = crowdsource.data.exists()
        if self.request.user.is_authenticated:
            user = self.request.user
            ip_address = None
        elif form.cleaned_data.get("email"):
            try:
                user = self.miniregister(
                    form,
                    form.cleaned_data["full_name"],
                    form.cleaned_data["email"],
                    form.cleaned_data.get("newsletter"),
                )
            except requests.exceptions.RequestException:
                return self.form_invalid(form)
            ip_address = None
        else:
            user = None
            ip_address, _ = get_client_ip(self.request)
        if user or ip_address:
            number = (
                self.object.responses.filter(
                    user=user, ip_address=ip_address, data=self.data
                ).count()
                + 1
            )
        else:
            number = 1
        if not has_data or self.data is not None:
            response = CrowdsourceResponse.objects.create(
                crowdsource=crowdsource,
                user=user,
                public=form.cleaned_data.get("public", False),
                ip_address=ip_address,
                data=self.data,
                number=number,
            )
            response.create_values(form.cleaned_data)
            messages.success(self.request, "Thank you!")
            properties = {
                "Crowdsource": crowdsource.title,
                "Crowdsource ID": crowdsource.pk,
                "Number": number,
            }
            if self.data:
                properties["Data"] = self.data.url
            mixpanel_event(self.request, "Assignment Completed", properties)
            for email in crowdsource.submission_emails.all():
                response.send_email(email.email)

        if self.request.POST.get("submit") == "Submit and Add Another":
            return self.render_to_response(self.get_context_data(data=self.data))

        if has_data:
            return redirect(
                "crowdsource-assignment", slug=crowdsource.slug, idx=crowdsource.pk
            )
        else:
            return redirect("crowdsource-list")

    def form_invalid(self, form):
        """Make sure we include the data in the context"""
        return self.render_to_response(self.get_context_data(form=form, data=self.data))

    def skip(self):
        """The user wants to skip this data"""
        crowdsource = self.get_object()
        ip_address, _ = get_client_ip(self.request)
        can_submit_anonymous = crowdsource.registration != "required" and ip_address
        if self.data is not None and self.request.user.is_authenticated:
            CrowdsourceResponse.objects.create(
                crowdsource=crowdsource,
                user=self.request.user,
                data=self.data,
                skip=True,
            )
            messages.info(self.request, "Skipped!")
        elif self.data is not None and can_submit_anonymous:
            CrowdsourceResponse.objects.create(
                crowdsource=crowdsource,
                ip_address=ip_address,
                data=self.data,
                skip=True,
            )
            messages.info(self.request, "Skipped!")
        return redirect(
            "crowdsource-assignment", slug=crowdsource.slug, idx=crowdsource.pk
        )


class CrowdsourceEditResponseView(BaseDetailView, FormView):
    """A view for an admin to edit a submitted response"""

    template_name = "crowdsource/form.html"
    form_class = CrowdsourceAssignmentForm
    pk_url_kwarg = "idx"
    context_object_name = "response"
    model = CrowdsourceResponse

    def dispatch(self, request, *args, **kwargs):
        """Check permissions"""
        # pylint: disable=attribute-defined-outside-init
        self.object = self.get_object()
        edit_perm = request.user.has_perm(
            "crowdsource.change_crowdsource", self.object.crowdsource
        )
        if not edit_perm:
            raise Http404
        return super(CrowdsourceEditResponseView, self).dispatch(
            request, *args, **kwargs
        )

    def get_form_kwargs(self):
        """Add the user and crowdsource object to the form"""
        kwargs = super(CrowdsourceEditResponseView, self).get_form_kwargs()
        kwargs.update(
            {"crowdsource": self.get_object().crowdsource, "user": self.request.user}
        )
        return kwargs

    def get_initial(self):
        """Fetch the crowdsource data item to show with this form,
        if there is one, and the latest values"""
        return self._get_initial("value")

    def _get_initial(self, value_attr):
        """Helper function to allow overriding of the value attribute for the
        revert view"""
        initial = {"data_id": self.object.data_id}
        for value in self.object.values.exclude(**{value_attr: ""}):
            key = str(value.field.pk)
            if key in initial:
                # if a single field has multiple values, make a list of values
                if isinstance(initial[key], list):
                    initial[key].append(getattr(value, value_attr))
                else:
                    initial[key] = [initial[key], getattr(value, value_attr)]
            else:
                initial[key] = getattr(value, value_attr)
        return initial

    def get_context_data(self, **kwargs):
        """Set the crowdsource and data in the context"""
        return super(CrowdsourceEditResponseView, self).get_context_data(
            crowdsource=self.object.crowdsource, data=self.object.data, edit=True
        )

    @transaction.atomic
    def form_valid(self, form):
        """Save the form results"""
        response = self.object
        response.edit_user = self.request.user
        response.edit_datetime = timezone.now()
        response.save()

        # remove non-assignment field fields
        form.cleaned_data.pop("data_id", None)
        form.cleaned_data.pop("public", None)
        for field_id, new_value in form.cleaned_data.items():
            field = CrowdsourceField.objects.filter(pk=field_id).first()
            if field and field.field.multiple_values:
                # for multi valued fields, collect all old and new values together
                # and recreate all values
                original_value = (
                    response.values.filter(field_id=field_id)
                    .exclude(original_value="")
                    .values_list("original_value", flat=True)
                )
                response.values.filter(field_id=field_id).delete()
                for orig, new in zip_longest(original_value, new_value, fillvalue=""):
                    response.values.create(
                        field_id=field_id, value=new, original_value=orig
                    )
            else:
                # for single valued field, just update the current value
                new_value = new_value if new_value is not None else ""
                response.values.update_or_create(
                    field_id=field_id, defaults={"value": new_value}
                )

        return redirect(
            "crowdsource-detail",
            slug=response.crowdsource.slug,
            idx=response.crowdsource.pk,
        )


class CrowdsourceRevertResponseView(CrowdsourceEditResponseView):
    """A view for an admin to revert a submitted response to its original values"""

    def get_initial(self):
        """Fetch the crowdsource data item to show with this form,
        if there is one, and the latest values"""
        return self._get_initial("original_value")


@method_decorator(xframe_options_exempt, name="dispatch")
class CrowdsourceEmbededFormView(CrowdsourceFormView):
    """A view to embed an assignment"""

    template_name = "crowdsource/embed.html"

    def form_valid(self, form):
        """Redirect to embedded confirmation page"""
        super(CrowdsourceEmbededFormView, self).form_valid(form)
        return redirect("crowdsource-embed-confirm")


@method_decorator(xframe_options_exempt, name="dispatch")
class CrowdsourceEmbededConfirmView(TemplateView):
    """Embedded confirm page"""

    template_name = "crowdsource/embed_confirm.html"


@method_decorator(xframe_options_exempt, name="dispatch")
class CrowdsourceEmbededGallery(DetailView):
    """Embedded gallery page"""

    template_name = "crowdsource/gallery.html"
    pk_url_kwarg = "idx"
    query_pk_and_slug = True
    queryset = Crowdsource.objects.exclude(status="draft")

    def get_context_data(self, **kwargs):
        """Get gallery fields"""
        context = super(CrowdsourceEmbededGallery, self).get_context_data(**kwargs)
        gallery_responses = self.object.responses.filter(gallery=True)
        context["values"] = CrowdsourceValue.objects.filter(
            response__in=gallery_responses, field__gallery=True
        ).values_list("value", flat=True)
        return context


class CrowdsourceListView(MRFilterListView):
    """List of crowdfunds"""

    model = Crowdsource
    template_name = "crowdsource/list.html"
    sort_map = {"title": "title", "user": "user"}
    filter_class = CrowdsourceFilterSet

    def get_queryset(self):
        """Get all open crowdsources and all crowdsources you own"""
        queryset = super(CrowdsourceListView, self).get_queryset()
        queryset = (
            queryset.select_related("user__profile", "project")
            .prefetch_related("data", "responses")
            .distinct()
        )
        return queryset.get_viewable(self.request.user)

    def get_context_data(self, **kwargs):
        """Remove filter for non-staff users"""
        context_data = super(CrowdsourceListView, self).get_context_data()
        if not self.request.user.is_staff:
            context_data.pop("filter", None)
        return context_data


class CrowdsourceCreateView(PermissionRequiredMixin, CreateView):
    """Create a crowdsource"""

    model = Crowdsource
    form_class = CrowdsourceForm
    template_name = "crowdsource/create.html"
    permission_required = "crowdsource.add_crowdsource"

    def get_context_data(self, **kwargs):
        """Add the data formset to the context"""
        data = super(CrowdsourceCreateView, self).get_context_data(**kwargs)
        if self.request.POST:
            data["data_formset"] = CrowdsourceDataFormset(self.request.POST)
        else:
            data["data_formset"] = CrowdsourceDataFormset(
                initial=[{"url": self.request.GET.get("initial_data")}]
            )
        return data

    def form_valid(self, form):
        """Save the crowdsource"""
        if self.request.POST.get("submit") == "start":
            status = "open"
            msg = "Crowdsource started"
        else:
            status = "draft"
            msg = "Crowdsource created"
        context = self.get_context_data()
        formset = context["data_formset"]
        crowdsource = form.save(commit=False)
        crowdsource.slug = slugify(crowdsource.title)
        crowdsource.user = self.request.user
        crowdsource.status = status
        crowdsource.save()
        form.save_m2m()
        crowdsource.create_form(form.cleaned_data["form_json"])
        form.process_data_csv(crowdsource)
        if formset.is_valid():
            formset.instance = crowdsource
            formset.save(doccloud_each_page=form.cleaned_data["doccloud_each_page"])
        messages.success(self.request, msg)
        return redirect(crowdsource)

    def get_form_kwargs(self):
        """Add user to form kwargs"""
        kwargs = super(CrowdsourceCreateView, self).get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


@class_view_decorator(login_required)
class CrowdsourceUpdateView(UpdateView):
    """Update a crowdsource"""

    model = Crowdsource
    form_class = CrowdsourceForm
    template_name = "crowdsource/create.html"
    pk_url_kwarg = "idx"
    query_pk_and_slug = True

    def dispatch(self, request, *args, **kwargs):
        """Check permissions"""
        # pylint: disable=attribute-defined-outside-init
        crowdsource = self.get_object()
        user_allowed = request.user.has_perm(
            "crowdsource.change_crowdsource", crowdsource
        )
        if not user_allowed:
            messages.error(request, "You may not edit this crowdsource")
            return redirect(crowdsource)
        if crowdsource.status != "draft":
            export_csv.delay(crowdsource.pk, self.request.user.pk)
            messages.info(
                self.request, "A CSV of the results so far will be emailed to you"
            )
        return super(CrowdsourceUpdateView, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        """Set the form JSON in the initial form data"""
        crowdsource = self.get_object()
        return {
            "form_json": crowdsource.get_form_json(),
            "submission_emails": ", ".join(
                str(e) for e in crowdsource.submission_emails.all()
            ),
        }

    def get_context_data(self, **kwargs):
        """Add the data formset to the context"""
        data = super(CrowdsourceUpdateView, self).get_context_data(**kwargs)
        CrowdsourceDataFormset.can_delete = True
        if self.request.POST:
            data["data_formset"] = CrowdsourceDataFormset(
                self.request.POST, instance=self.get_object()
            )
        else:
            data["data_formset"] = CrowdsourceDataFormset(instance=self.get_object())
        return data

    def form_valid(self, form):
        """Save the crowdsource"""
        if self.request.POST.get("submit") == "start":
            status = "open"
            msg = "Crowdsource started"
        else:
            status = "draft"
            msg = "Crowdsource updated"
        context = self.get_context_data()
        formset = context["data_formset"]
        crowdsource = form.save(commit=False)
        crowdsource.slug = slugify(crowdsource.title)
        crowdsource.status = status
        crowdsource.save()
        form.save_m2m()
        crowdsource.create_form(form.cleaned_data["form_json"])
        form.process_data_csv(crowdsource)
        if formset.is_valid():
            formset.save(doccloud_each_page=form.cleaned_data["doccloud_each_page"])
        messages.success(self.request, msg)
        return redirect(crowdsource)

    def get_form_kwargs(self):
        """Add user to form kwargs"""
        kwargs = super(CrowdsourceUpdateView, self).get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


def oembed(request):
    """AJAX view to get oembed data"""
    if "url" in request.GET:
        data = CrowdsourceData(url=request.GET["url"])
        return HttpResponse(data.embed())
    else:
        return HttpResponseBadRequest()


def message_response(request):
    """AJAX view to send an email to the user of a response"""
    form = CrowdsourceMessageResponseForm(request.POST)
    if form.is_valid():
        response = form.cleaned_data["response"]
        if not request.user.has_perm(
            "crowdsource.change_crowdsource", response.crowdsource
        ):
            return JsonResponse({"error": "permission denied"}, status=403)
        if not response.user or not response.user.email:
            return JsonResponse({"error": "no email"}, status=400)
        msg = TemplateEmail(
            subject=form.cleaned_data["subject"],
            reply_to=[request.user.email],
            user=response.user,
            text_template="crowdsource/email/message_user.txt",
            html_template="crowdsource/email/message_user.html",
            extra_context={
                "body": form.cleaned_data["body"],
                "assignment": response.crowdsource,
                "from_user": request.user,
            },
        )
        msg.send()
        return JsonResponse({"status": "ok"})
    else:
        return JsonResponse({"error": "form invalid"}, status=400)


class CrowdsourceAutocomplete(MRAutocompleteView):
    """Autocomplete for assignments"""

    model = Crowdsource
    search_fields = ["title", "description"]

    def get_queryset(self):
        """Only show drafts by the current user"""
        queryset = super().get_queryset()
        return queryset.filter(status="draft", user=self.request.user)
