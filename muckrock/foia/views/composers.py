"""
FOIA views for composing
"""

# Django
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.encoding import smart_text
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, UpdateView

# Standard Library
import re

# Third Party
import requests

# MuckRock
from muckrock.accounts.mixins import BuyRequestsMixin, MiniregMixin
from muckrock.accounts.utils import mixpanel_event
from muckrock.agency.models import Agency
from muckrock.foia.exceptions import InsufficientRequestsError
from muckrock.foia.forms import BaseComposerForm, ComposerForm, ContactInfoForm
from muckrock.foia.models import FOIAComposer, FOIARequest


def format_org_list(organizations):
    """Return a comma separated list of organizations for display"""

    organizations = list(organizations)

    def name(organization):
        """Display name for the organization"""
        if organization.individual:
            return "your personal account"
        else:
            return organization.name

    if len(organizations) == 0:
        return ""
    elif len(organizations) == 1:
        return name(organizations[0])
    elif len(organizations) == 2:
        return "{} or {}".format(name(organizations[0]), name(organizations[1]))
    elif len(organizations) > 2:
        formatted = ", ".join(name(o) for o in organizations[:-1])
        return "{}, or {}".format(formatted, name(organizations[-1]))


class GenericComposer(BuyRequestsMixin):
    """Shared functionality between create and update composer views"""

    template_name = "forms/foia/create.html"
    form_class = ComposerForm
    context_object_name = "composer"

    def _get_organizations(self, user):
        """Get the active organization and which organization should pay
        This is the active org if the user is an admin of that org,
        else it is the user's individual org
        """
        if not user.is_authenticated:
            return None, None
        active = user.profile.organization
        if active.has_admin(user):
            payer = active
        else:
            payer = user.profile.individual_organization
        return (active, payer)

    def get_form_kwargs(self):
        """Add request to the form kwargs"""
        kwargs = super(GenericComposer, self).get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["request"] = self.request
        _, payer = self._get_organizations(self.request.user)
        kwargs["organization"] = payer

        if len(self.request.POST.getlist("agencies")) == 1:
            # pass the agency for contact info form
            try:
                kwargs["agency"] = Agency.objects.get(
                    pk=self.request.POST.get("agencies")
                )
            except (Agency.DoesNotExist, ValueError):
                # ValueError for new agency format
                pass
        return kwargs

    def get_context_data(self, **kwargs):
        """Extra context"""
        context = super(GenericComposer, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            foias_filed = self.request.user.composers.exclude(status="started").count()
            organization, payer = self._get_organizations(self.request.user)
            context["organization"] = organization
            context["payer"] = payer
            context["other_organizations"] = format_org_list(
                self.request.user.organizations.exclude(pk=organization.pk)
            )
            context["request_organizations"] = format_org_list(
                self.request.user.organizations.exclude(pk=organization.pk).filter(
                    Q(monthly_requests__gt=0) | Q(number_requests__gt=0)
                )
            )
            requests_left = {
                "regular": organization.number_requests,
                "monthly": organization.monthly_requests,
            }
            context["sidebar_admin_url"] = reverse(
                "admin:foia_foiacomposer_change", args=(self.object.pk,)
            )
        else:
            foias_filed = 0
            requests_left = {}
        context.update(
            {
                "settings": settings,
                "foias_filed": foias_filed,
                "requests_left": requests_left,
                "stripe_pk": settings.STRIPE_PUB_KEY,
            }
        )
        return context

    def get_initial(self):
        """Set the initial value for tags"""
        return {"tags": self.object.tags.all()}

    def _submit_composer(self, composer, form):
        """Submit a composer"""
        # pylint: disable=not-an-iterable
        if composer.attachments_over_size_limit(self.request.user):
            messages.error(self.request, "Total attachment size must be less than 20MB")
            return
        num_requests = form.cleaned_data.get("num_requests", 0)
        num_requests = 0 if num_requests is None else num_requests
        if num_requests > 0:
            active, payer = self._get_organizations(self.request.user)
            self.buy_requests(form, active, payer)
        if (
            form.cleaned_data.get("use_contact_information")
            and self.request.user.has_perm("foia.set_info_foiarequest")
            and len(composer.agencies.all()) == 1
        ):
            contact_info = {
                k: form.cleaned_data.get(k) for k in ContactInfoForm.base_fields
            }
        else:
            contact_info = None
        try:
            composer.submit(contact_info, form.cleaned_data.get("no_proxy"))
        except InsufficientRequestsError:
            messages.warning(self.request, "You need to purchase more requests")
        else:
            self.request.session["ga"] = "request_submitted"
            mixpanel_event(
                self.request,
                "Request Submitted",
                self._composer_mixpanel_properties(composer),
            )
            warning = self._proxy_warnings(composer)
            if warning:
                messages.warning(self.request, warning)

    def _proxy_warnings(self, composer):
        """Check composer's agencies for proxy status"""
        proxies = {"missing": 0, "non-missing": 0}
        for agency in composer.agencies.all():
            proxy_info = agency.get_proxy_info()
            if proxy_info["proxy"] and proxy_info["missing_proxy"]:
                proxies["missing"] += 1
            elif proxy_info["proxy"] and not proxy_info["missing_proxy"]:
                proxies["non-missing"] += 1
        if proxies["missing"] and proxies["non-missing"]:
            return (
                "Some of the agencies you are requesting from require "
                "requestors to be in-state citizens.  We will file these "
                "with volunteer filers in states in which we have a "
                "volunteer available.  If we do not have a volunteer "
                "available, your request will be filed in your name."
            )
        elif proxies["missing"]:
            return (
                "Some of the agencies you are requesting from require "
                "requestors to be in-state citizens.  We do not currently "
                "have a citizen proxy requestor on file for these "
                "agencies, so we will file this request in your name."
            )
        elif proxies["non-missing"]:
            return (
                "Some of the agencies you are requesting from require "
                "requestors to be in-state citizens.  These requests will "
                "be filed in the name of one of our volunteer files for "
                "these states."
            )
        else:
            return ""

    def _composer_mixpanel_properties(self, composer):
        """Get properties for tracking composer events in mixpanel"""
        return {
            "Number": len(composer.agencies.all()),
            "Title": composer.title,
            "Agencies": [a.name for a in composer.agencies.all()],
            "Embargo": composer.embargo,
            "Permanent Embargo": composer.permanent_embargo,
            "Created At": composer.datetime_created.isoformat(),
            "Parent": composer.parent.pk if composer.parent else None,
            "ID": composer.pk,
        }


class CreateComposer(MiniregMixin, GenericComposer, CreateView):
    """Create a new composer"""

    minireg_source = "Composer"
    field_map = {"email": "register_email", "name": "register_full_name"}

    # pylint: disable=attribute-defined-outside-init

    def get_initial(self):
        """Get initial data from clone, if there is one"""
        self.clone = None
        # set title to blank, as if we create a new empty draft, it will
        # set the title to 'Untitled'
        data = {"title": ""}
        clone_pk = self.request.GET.get("clone")
        if clone_pk is not None:
            data.update(self._get_clone_data(clone_pk))
        agency_pks = self.request.GET.getlist("agency")
        agency_pks = [pk for pk in agency_pks if re.match("^[0-9]+$", pk)]
        if agency_pks:
            agencies = Agency.objects.filter(pk__in=agency_pks, status="approved")
            data.update({"agencies": agencies})
        return data

    def _get_clone_data(self, clone_pk):
        """Get the intial data for a clone"""
        try:
            composer = get_object_or_404(FOIAComposer, pk=clone_pk)
        except ValueError:
            # non integer passed in as clone_pk
            return {}
        if not composer.has_perm(self.request.user, "view"):
            raise Http404()
        initial_data = {
            "title": composer.title,
            "requested_docs": smart_text(composer.requested_docs),
            "agencies": composer.agencies.all(),
            "tags": composer.tags.all(),
            "edited_boilerplate": composer.edited_boilerplate,
            "parent": composer,
        }
        self.clone = composer
        mixpanel_event(
            self.request, "Request Cloned", self._composer_mixpanel_properties(composer)
        )
        return initial_data

    def get_context_data(self, **kwargs):
        """Extra context"""
        # if user is authenticated, save an empty draft to the database
        # so that autosaving and file uploading will work
        if self.request.user.is_authenticated:
            self.object = FOIAComposer.objects.get_or_create_draft(
                user=self.request.user,
                organization=self.request.user.profile.organization,
            )
        context = super(CreateComposer, self).get_context_data(**kwargs)
        context.update(
            {
                "clone": self.clone,
                "featured": FOIARequest.objects.get_featured(self.request.user),
            }
        )
        return context

    def _handle_anonymous_submitter(self, form):
        """Handle a submission from an anonymous user"""
        # form validation guarentees we have either registration or login info
        # pylint: disable=protected-access
        if form.cleaned_data.get("register_full_name"):
            user = self.miniregister(
                form,
                form.cleaned_data["register_full_name"],
                form.cleaned_data["register_email"],
                form.cleaned_data.get("register_newsletter"),
            )
            return user
        else:
            login(self.request, form._user)
            return form._user

    def form_valid(self, form):
        """Create the request"""
        if self.request.user.is_authenticated:
            user = self.request.user
        else:
            try:
                user = self._handle_anonymous_submitter(form)
            except requests.exceptions.RequestException:
                return self.form_invalid(form)
        if form.cleaned_data["action"] in ("save", "submit"):
            composer = form.save()
            # if a new agency is added while the user is anonymous,
            # we want to associate that agency to the user once they
            # login or register
            composer.agencies.filter(user=None, status="pending").update(user=user)
        if form.cleaned_data["action"] == "save":
            self.request.session["ga"] = "request_drafted"
            mixpanel_event(
                self.request,
                "Request Saved",
                self._composer_mixpanel_properties(composer),
            )
            messages.success(self.request, "Request saved")
        elif form.cleaned_data["action"] == "submit":
            self._submit_composer(composer, form)
        return redirect(composer)


class UpdateComposer(LoginRequiredMixin, GenericComposer, UpdateView):
    """Update a composer"""

    # pylint: disable=attribute-defined-outside-init
    pk_url_kwarg = "idx"

    def get_queryset(self):
        """Restrict to composers you can view"""
        kwargs = {}
        # non staff may only see their own requests
        if not self.request.user.is_staff:
            kwargs["user"] = self.request.user
        # can only post to draft composers
        if self.request.method == "POST":
            kwargs["status"] = "started"
        return FOIAComposer.objects.filter(**kwargs)

    def get_object(self, queryset=None):
        """Convert object back to draft if it has been submitted recently"""
        composer = super(UpdateComposer, self).get_object(queryset)
        if composer.revokable():
            composer.revoke()
            messages.warning(
                self.request,
                "This request's submission has been cancelled.  You may now "
                "edit it and submit it again when ready",
            )
        return composer

    def post(self, request, *args, **kwargs):
        """Allow deletion regardless of form validation"""
        self.object = self.get_object()
        if request.POST.get("action") == "delete":
            if self.object.has_perm(request.user, "delete"):
                self.object.delete()
                messages.success(self.request, "Draft deleted")
                return redirect("foia-mylist-drafts")
            else:
                messages.success(
                    self.request, "You do not have permission to delete that draft"
                )
                return redirect("foia-mylist-drafts")
        return super(UpdateComposer, self).post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        """Redirect if this composer is not a draft"""
        self.object = self.get_object()
        if self.object.status != "started":
            messages.warning(self.request, "This request can no longer be updated.")
            return redirect(self.object)
        else:
            return self.render_to_response(self.get_context_data())

    def form_valid(self, form):
        """Update the request"""
        if form.cleaned_data["action"] == "save":
            composer = form.save()
            self.request.session["ga"] = "request_drafted"
            mixpanel_event(
                self.request,
                "Request Saved",
                self._composer_mixpanel_properties(composer),
            )
            messages.success(self.request, "Request saved")
        elif form.cleaned_data["action"] == "submit":
            composer = form.save()
            self._submit_composer(composer, form)
        return redirect(composer)


@login_required
@require_POST
def autosave(request, idx):
    """Save the composer via AJAX"""
    composer = get_object_or_404(
        FOIAComposer, pk=idx, status="started", user=request.user
    )
    old_agencies = set(composer.agencies.all())
    data = request.POST.copy()
    # we are always just saving
    data["action"] = "save"
    form = BaseComposerForm(data, instance=composer, user=request.user, request=request)
    if form.is_valid():
        composer = form.save(update_owners=False, commit=False)
        fields = {
            f: getattr(composer, f)
            for f in form.cleaned_data
            if f not in ("agencies", "tags", "no_proxy", "action")
        }
        with transaction.atomic():
            # ensure that the status is still started
            # otherwise there is a race condition where the auto save is overriding
            # the status back to started after it has been submitted
            updated = FOIAComposer.objects.filter(
                pk=composer.pk, status="started"
            ).update(**fields)
            if updated:
                form.save_m2m()
        new_agencies = set(composer.agencies.all())
        removed_agencies = old_agencies - new_agencies
        # delete pending agencies which have been removed from composers and requests
        for agency in removed_agencies:
            if (
                agency.status == "pending"
                and agency.composers.count() == 0
                and agency.foiarequest_set.count() == 0
            ):
                agency.delete()
        return HttpResponse("OK")
    else:
        return HttpResponseBadRequest(form.errors.as_json())
