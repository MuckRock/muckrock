"""Handle POST actions for the FOIA detail view"""

# Django
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone

# Standard Library
import itertools
import logging
import sys

# Third Party
import requests

# MuckRock
from muckrock.accounts.utils import mixpanel_event
from muckrock.agency.forms import AgencyForm
from muckrock.communication.models import WebCommunication
from muckrock.core.utils import new_action
from muckrock.foia.exceptions import FoiaFormError
from muckrock.foia.forms import (
    ContactInfoForm,
    FOIAAccessForm,
    FOIAAdminFixForm,
    FOIAAgencyReplyForm,
    FOIAContactUserForm,
    FOIAEstimatedCompletionDateForm,
    FOIAFlagForm,
    FOIANoteForm,
    FOIASoftDeleteForm,
    RequestFeeForm,
    ResendForm,
    TrackingNumberForm,
)
from muckrock.foia.forms.comms import AgencyPasscodeForm
from muckrock.foia.models import STATUS, FOIACommunication, FOIAFile, FOIARequest
from muckrock.foia.tasks import import_doccloud_file
from muckrock.jurisdiction.forms import AppealForm
from muckrock.jurisdiction.models import Appeal
from muckrock.message.email import TemplateEmail
from muckrock.portal.forms import PortalForm
from muckrock.project.forms import ProjectManagerForm
from muckrock.task.models import FlaggedTask, ResponseTask, StatusChangeTask

logger = logging.getLogger(__name__)


def _get_redirect(request, foia):
    """Get the redirect URL"""
    if "agency" in request.GET:
        param = "?agency"
    else:
        param = ""
    return redirect("{}{}#".format(foia.get_absolute_url(), param))


def tags(request, foia):
    """Handle updating tags"""
    if foia.has_perm(request.user, "change"):
        foia.update_tags(request.POST.getlist("tags"))
    return _get_redirect(request, foia)


def projects(request, foia):
    """Handle updating projects"""
    form = ProjectManagerForm(request.POST, user=request.user)
    has_perm = foia.has_perm(request.user, "change")
    if has_perm and form.is_valid():
        projects_ = form.cleaned_data["projects"]
        for proj in itertools.chain(foia.projects.all(), projects_):
            # clear cache for old and new projects
            proj.clear_cache()
        foia.projects.set(projects_)
    return _get_redirect(request, foia)


def status(request, foia):
    """Handle updating status"""
    allowed_statuses = [s for s, _ in STATUS if s != "submitted"]
    status_ = request.POST.get("status")
    old_status = foia.get_status_display()
    has_perm = foia.has_perm(request.user, "change")
    user_editable = has_perm and status_ in allowed_statuses
    staff_editable = request.user.is_staff and status_ in allowed_statuses
    if foia.status != "submitted" and (user_editable or staff_editable):
        foia.status = status_
        foia.save(comment="status updated")
        if staff_editable:
            kwargs = {
                "resolved": True,
                "resolved_by": request.user,
                "date_done": timezone.now(),
            }
        else:
            kwargs = {}
        StatusChangeTask.objects.create(
            user=request.user, old_status=old_status, foia=foia, **kwargs
        )
        response_tasks = ResponseTask.objects.filter(
            resolved=False, communication__foia=foia
        )
        for task in response_tasks:
            task.resolve(request.user)
    return _get_redirect(request, foia)


def add_note(request, foia):
    """Adds a note to the request"""
    note_form = FOIANoteForm(request.POST)
    has_perm = foia.has_perm(request.user, "change")
    if has_perm and note_form.is_valid():
        foia_note = note_form.save(commit=False)
        foia_note.foia = foia
        foia_note.author = request.user
        foia_note.datetime = timezone.now()
        foia_note.save()
        logger.info("%s added %s to %s", foia_note.author, foia_note, foia_note.foia)
        messages.success(request, "Your note is attached to the request.")
    return _get_redirect(request, foia)


def flag(request, foia):
    """Allow a user to notify us of a problem with the request"""
    form = FOIAFlagForm(request.POST, all_choices=True)
    if form.is_valid():
        FlaggedTask.objects.create(
            user=request.user if request.user.is_authenticated else None,
            foia=foia,
            text=form.cleaned_data["text"],
            category=form.cleaned_data["category"],
        )
        messages.success(request, "Problem succesfully reported")
        if request.user.is_authenticated:
            new_action(request.user, "flagged", target=foia)
    return _get_redirect(request, foia)


def delete(request, foia):
    """Allow staff to soft delete requests"""
    form = FOIASoftDeleteForm(request.POST, foia=foia)
    has_perm = request.user.has_perm("foia.delete_foiarequest")
    if has_perm and form.is_valid():
        foia.soft_delete(
            request.user,
            # final message is not used when foia is in an end state
            form.cleaned_data.get("final_message", ""),
            form.cleaned_data["note"],
        )
        messages.success(request, "Request succesfully deleted")
    return _get_redirect(request, foia)


def contact_user(request, foia):
    """Allow an admin to message the foia's owner"""
    form = FOIAContactUserForm(request.POST)
    if request.user.is_staff and form.is_valid() and form.cleaned_data["text"]:
        context = {
            "text": form.cleaned_data["text"],
            "foia_url": foia.user.profile.wrap_url(foia.get_absolute_url()),
            "foia_title": foia.title,
        }
        email = TemplateEmail(
            user=foia.user,
            extra_context=context,
            text_template="message/notification/contact_user.txt",
            html_template="message/notification/contact_user.html",
            subject="Message from MuckRock",
        )
        email.send(fail_silently=False)
        messages.success(request, "Email sent to %s" % foia.user.email)
    return _get_redirect(request, foia)


def follow_up(request, foia):
    """Handle submitting follow ups"""
    if request.user.is_anonymous:
        messages.error(request, "You must be logged in to follow up")
        return _get_redirect(request, foia)
    if foia.attachments_over_size_limit(request.user):
        messages.error(request, "Total attachment size must be less than 20MB")
        return _get_redirect(request, foia)
    if request.user.is_staff:
        return _admin_follow_up(request, foia)
    else:
        return _user_follow_up(request, foia)


def _admin_follow_up(request, foia):
    """Handle follow ups for admins"""
    form = FOIAAdminFixForm(
        request.POST, prefix="admin_fix", request=request, foia=foia
    )
    if form.is_valid():
        foia.update_address(
            form.cleaned_data["via"],
            email=form.cleaned_data["email"],
            other_emails=form.cleaned_data["other_emails"],
            fax=form.cleaned_data["fax"],
        )
        snail = form.cleaned_data["via"] == "snail"
        foia.create_out_communication(
            from_user=form.cleaned_data["from_user"],
            text=form.cleaned_data["comm"],
            user=request.user,
            snail=snail,
            subject=form.cleaned_data["subject"],
        )
        messages.success(request, "Your follow up has been sent.")
        new_action(request.user, "followed up on", target=foia)
        return _get_redirect(request, foia)
    else:
        raise FoiaFormError("admin_fix_form", form)


def _user_follow_up(request, foia):
    """Handle follow ups for non-admins"""
    has_perm = foia.has_perm(request.user, "followup")
    contact_info_form = ContactInfoForm(request.POST, foia=foia, prefix="followup")
    has_contact_perm = request.user.has_perm("foia.set_info_foiarequest")
    contact_valid = contact_info_form.is_valid()
    use_contact_info = has_contact_perm and contact_info_form.cleaned_data.get(
        "use_contact_information"
    )
    comm_sent = _new_comm(
        request,
        foia,
        has_perm and (not use_contact_info or contact_valid),
        "Your follow up has been sent.",
        contact_info=contact_info_form.cleaned_data if use_contact_info else None,
    )
    if use_contact_info:
        foia.add_contact_info_note(request.user, contact_info_form.cleaned_data)
    if comm_sent:
        new_action(request.user, "followed up on", target=foia)
        mixpanel_event(
            request,
            "Follow Up",
            foia.mixpanel_data({"Use Contact Info": use_contact_info}),
        )
    return _get_redirect(request, foia)


def thanks(request, foia):
    """Handle submitting a thank you follow up"""
    success_msg = "Your thank you has been sent."
    has_perm = foia.has_perm(request.user, "thank")
    comm_sent = _new_comm(request, foia, has_perm, success_msg, thanks=True)
    if comm_sent:
        new_action(request.user, verb="thanked", target=foia.agency)
    return _get_redirect(request, foia)


def _new_comm(request, foia, test, success_msg, **kwargs):
    """Helper function for sending a new comm"""
    # pylint: disable=too-many-arguments
    text = request.POST.get("text")
    comm_sent = False
    if text and test:
        foia.create_out_communication(
            from_user=request.user, text=text, user=request.user, **kwargs
        )
        messages.success(request, success_msg)
        comm_sent = True
    return comm_sent


def appeal(request, foia):
    """Handle submitting an appeal, then create an Appeal from the returned
    communication.
    """
    form = AppealForm(request.POST)
    has_perm = foia.has_perm(request.user, "appeal")
    contact_info_form = ContactInfoForm(
        request.POST, foia=foia, prefix="appeal", appeal=True
    )
    has_contact_perm = request.user.has_perm("foia.set_info_foiarequest")
    contact_valid = contact_info_form.is_valid()
    use_contact_info = has_contact_perm and contact_info_form.cleaned_data.get(
        "use_contact_information"
    )
    if not has_perm:
        messages.error(request, "You do not have permission to submit an appeal.")
        return _get_redirect(request, foia)
    if not form.is_valid():
        messages.error(request, "You did not submit an appeal.")
        return _get_redirect(request, foia)
    if foia.attachments_over_size_limit(request.user):
        messages.error(request, "Total attachment size must be less than 20MB")
        return _get_redirect(request, foia)
    if use_contact_info and not contact_valid:
        messages.error(request, "Invalid contact information")
        return _get_redirect(request, foia)
    communication = foia.appeal(
        form.cleaned_data["text"],
        request.user,
        contact_info=contact_info_form.cleaned_data if use_contact_info else None,
    )
    base_language = form.cleaned_data["base_language"]
    appeal_ = Appeal.objects.create(communication=communication)
    appeal_.base_language.set(base_language)
    new_action(request.user, "appealed", target=foia)
    messages.success(request, "Your appeal has been sent.")
    if use_contact_info:
        foia.add_contact_info_note(request.user, contact_info_form.cleaned_data)
    return _get_redirect(request, foia)


def date_estimate(request, foia):
    """Change the estimated completion date"""
    form = FOIAEstimatedCompletionDateForm(request.POST, instance=foia)
    if foia.has_perm(request.user, "change"):
        if form.is_valid():
            form.save()
            messages.success(
                request, "Successfully changed the estimated completion date."
            )
        else:
            messages.error(request, "Invalid date provided.")
    else:
        messages.error(request, "You cannot do that, stop it.")
    return _get_redirect(request, foia)


def tracking_id(request, foia):
    """Add a new tracking ID"""
    form = TrackingNumberForm(request.POST)
    if request.user.is_staff:
        if form.is_valid():
            tracking_id_ = form.save(commit=False)
            tracking_id_.foia = foia
            tracking_id_.save()
            messages.success(request, "Successfully added a tracking number")
        else:
            messages.error(request, "Please fill out the tracking number and reason")
    else:
        messages.error(request, "You do not have permission to do that")
    return _get_redirect(request, foia)


def portal(request, foia):
    """Add a new or existing portal"""
    form = PortalForm(request.POST, foia=foia)
    if request.user.is_staff:
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully added a portal")
        else:
            messages.error(
                request, "Choose a portal or supply information for a new one"
            )
    else:
        messages.error(request, "You do not have permission to do that")
    return _get_redirect(request, foia)


def update_new_agency(request, foia):
    """Update the new agency"""
    form = AgencyForm(
        request.POST, instance=foia.agency, prefix=request.POST.get("task", "")
    )
    if foia.has_perm(request.user, "change"):
        if form.is_valid():
            form.save()
            messages.success(request, "Agency info saved. Thanks for your help!")
        else:
            messages.error(request, "The data was invalid! Try again.")
    else:
        messages.error(request, "You cannot do that, stop it.")
    return _get_redirect(request, foia)


def generate_key(request, foia):
    """Generate and return an access key, with support for AJAX."""
    if not foia.has_perm(request.user, "change"):
        if request.is_ajax():
            return PermissionDenied
        else:
            return _get_redirect(request, foia)
    else:
        key = foia.generate_access_key()
        if request.is_ajax():
            return JsonResponse({"key": key})
        else:
            messages.success(request, "New private link created.")
            return _get_redirect(request, foia)


def grant_access(request, foia):
    """Grant editor access to the specified users."""
    form = FOIAAccessForm(request.POST)
    has_perm = foia.has_perm(request.user, "change")
    if not has_perm or not form.is_valid():
        return _get_redirect(request, foia)
    access = form.cleaned_data["access"]
    users = form.cleaned_data["users"]
    if access == "edit" and users:
        for user in users:
            foia.add_editor(user)
    if access == "view" and users:
        for user in users:
            foia.add_viewer(user)
    if len(users) > 1:
        success_msg = "%d people can now %s this request." % (len(users), access)
    else:
        success_msg = "%s can now %s this request." % (
            users[0].profile.full_name,
            access,
        )
    messages.success(request, success_msg)
    return _get_redirect(request, foia)


def revoke_access(request, foia):
    """Revoke access from a user."""
    user_pk = request.POST.get("user")
    user = User.objects.get(pk=user_pk)
    has_perm = foia.has_perm(request.user, "change")
    if has_perm and user:
        if foia.has_editor(user):
            foia.remove_editor(user)
        elif foia.has_viewer(user):
            foia.remove_viewer(user)
        messages.success(
            request, "%s no longer has access to this request." % user.profile.full_name
        )
    return _get_redirect(request, foia)


def demote(request, foia):
    """Demote user from editor access to viewer access"""
    user_pk = request.POST.get("user")
    user = User.objects.get(pk=user_pk)
    has_perm = foia.has_perm(request.user, "change")
    if has_perm and user:
        foia.demote_editor(user)
        messages.success(
            request, "%s can now only view this request." % user.profile.full_name
        )
    return _get_redirect(request, foia)


def promote(request, foia):
    """Promote user from viewer access to editor access"""
    user_pk = request.POST.get("user")
    user = User.objects.get(pk=user_pk)
    has_perm = foia.has_perm(request.user, "change")
    if has_perm and user:
        foia.promote_viewer(user)
        messages.success(
            request, "%s can now edit this request." % user.profile.full_name
        )
    return _get_redirect(request, foia)


def agency_reply(request, foia):
    """Agency reply directly through the site"""
    has_perm = foia.has_perm(request.user, "agency_reply")
    valid_passcode = request.session.get(f"foiapasscode:{foia.pk}")

    if has_perm or valid_passcode:
        form = FOIAAgencyReplyForm(request.POST)
        if form.is_valid():
            agency_user = (
                request.user
                if request.user.is_authenticated
                else foia.agency.get_user()
            )
            comm = FOIACommunication.objects.create(
                foia=foia,
                from_user=agency_user,
                to_user=foia.user,
                response=True,
                datetime=timezone.now(),
                communication=form.cleaned_data["reply"],
                status=form.cleaned_data["status"],
                hidden=not has_perm,
            )
            WebCommunication.objects.create(
                communication=comm, sent_datetime=timezone.now()
            )
            foia.date_estimate = form.cleaned_data["date_estimate"]
            foia.add_tracking_id(form.cleaned_data["tracking_id"])
            foia.status = form.cleaned_data["status"]
            if foia.status == "payment":
                foia.price = form.cleaned_data["price"] / 100.0
            foia.save()
            foia.process_attachments(agency_user)
            comm.create_agency_notifications()
            if has_perm:
                text = "An agency used a secure login to update this request"
                category = "agency login confirm"
            else:
                text = (
                    "An agency used an insecure login to update this request. (Hidden)"
                    "\n\nPlease review it and show it if appropriate"
                )
                category = "agency login validate"
            FlaggedTask.objects.create(
                user=agency_user, foia=foia, text=text, category=category
            )
            messages.success(
                request,
                "Thank you for your message! We’ll alert the user and they’ll be "
                "able to respond as required. If you need to reach our staff, "
                'click the "Get Help" button.',
            )
        else:
            raise FoiaFormError("agency_reply_form", form)

    return _get_redirect(request, foia)


def staff_pay(request, foia):
    """Staff pays for a request without using stripe"""
    has_perm = request.user.is_staff
    if has_perm:
        amount = request.POST.get("amount")
        try:
            amount = int(amount)
        except (ValueError, TypeError):
            messages.error(request, "Not a valid amount")
        else:
            foia.pay(request.user, amount / 100.0)
    return _get_redirect(request, foia)


def pay_fee(request, foia):
    """A user pays the fee for a request"""
    form = RequestFeeForm(request.POST, user=request.user)
    if not request.user.is_authenticated:
        messages.error(request, "Must be logged in to pay")
        return _get_redirect(request, foia)
    if form.is_valid():
        with transaction.atomic():
            try:
                locked_foia = FOIARequest.objects.select_for_update().get(pk=foia.pk)
                if locked_foia.status != "payment":
                    messages.warning(
                        request,
                        "This request no longer requires payment.  This prevents "
                        "you from being charged twice for this request.  Your "
                        "first payment should have been processed.",
                    )
                    return _get_redirect(request, foia)
                locked_foia.status = "submitted"
                locked_foia.save()
                form.cleaned_data["organization"].pay(
                    amount=int(form.cleaned_data["amount"] * 1.05),
                    fee_amount=5,
                    description="Pay ${:.2f} fee for request #{}".format(
                        form.cleaned_data["amount"] / 100.0, foia.pk
                    ),
                    token=form.cleaned_data["stripe_token"],
                    save_card=form.cleaned_data["save_card"],
                )
            except requests.exceptions.RequestException as exc:
                locked_foia.status = "payment"
                locked_foia.save()
                logger.warning("Payment error: %s", exc, exc_info=sys.exc_info())
                if exc.response.status_code // 100 == 4:
                    messages.error(
                        request,
                        "Payment Error: {}".format(
                            "\n".join(
                                "{}: {}".format(k, v)
                                for k, v in exc.response.json().items()
                            )
                        ),
                    )
                else:
                    messages.error(request, "Payment Error")
                return _get_redirect(request, foia)
            else:
                messages.success(
                    request,
                    "Your payment was successful. "
                    "We will get this to the agency right away!",
                )
                foia.status = locked_foia.status
                amount = form.cleaned_data["amount"] / 100.0
                foia.pay(request.user, amount)
                mixpanel_event(
                    request,
                    "Request Fee Paid",
                    foia.mixpanel_data({"Price": amount}),
                    charge=amount,
                )
                return _get_redirect(request, foia)
    else:
        raise FoiaFormError("fee_form", form)


def resend_comm(request, foia):
    """Resend a communication"""
    if request.user.is_staff:
        form = ResendForm(request.POST, prefix=request.POST.get("communication", ""))
        if form.is_valid():
            foia.update_address(
                form.cleaned_data["via"],
                email=form.cleaned_data["email"],
                fax=form.cleaned_data["fax"],
            )
            snail = form.cleaned_data["via"] == "snail"
            foia.submit(snail=snail, comm=form.cleaned_data["communication"])
            messages.success(request, "The communication was resent")
        else:
            comm = form.cleaned_data.get("communication")
            raise FoiaFormError("resend_form", form, comm_id=comm.id if comm else None)
    return _get_redirect(request, foia)


def move_comm(request, foia):
    """Admin moves a communication to a different FOIA"""
    if request.user.is_staff:
        try:
            comm_pk = request.POST["comm_pk"]
            comm = FOIACommunication.objects.get(pk=comm_pk)
            new_foia_pks = request.POST["new_foia_pks"].split(",")
            comm.move(new_foia_pks, request.user)
            messages.success(request, "Communication moved successfully")
        except (KeyError, FOIACommunication.DoesNotExist):
            messages.error(request, "The communication does not exist.")
        except ValueError:
            messages.error(request, "No move destination provided.")
    return _get_redirect(request, foia)


def delete_comm(request, foia):
    """Admin deletes a communication"""
    if request.user.is_staff:
        try:
            comm = FOIACommunication.objects.get(pk=request.POST["comm_pk"])
            files = comm.files.all()
            for file_ in files:
                file_.delete()
            comm.delete()
            messages.success(request, "The communication was deleted.")
        except (KeyError, FOIACommunication.DoesNotExist):
            messages.error(request, "The communication does not exist.")
    return _get_redirect(request, foia)


def status_comm(request, foia):
    """Change the status of a communication"""
    if request.user.is_staff:
        try:
            comm = FOIACommunication.objects.get(pk=request.POST["comm_pk"])
            status_ = request.POST.get("status", "")
            if status_ in [s for s, _ in STATUS]:
                comm.status = status_
                comm.save()
        except (KeyError, FOIACommunication.DoesNotExist):
            messages.error(request, "The communication does not exist.")
    return _get_redirect(request, foia)


def agency_passcode(request, foia):
    """Allow an agency to authenticate using the passcode"""
    form = AgencyPasscodeForm(request.POST, foia=foia)
    if form.is_valid():
        request.session[f"foiapasscode:{foia.pk}"] = True
        request.session.set_expiry(settings.AGENCY_SESSION_TIME)
        return _get_redirect(request, foia)
    else:
        raise FoiaFormError("agency_passcode_form", form)


def import_dc_file(request, foia):
    """Import a file from DocumentCloud"""
    if request.user.is_staff:
        file_pk = request.POST.get("file_pk")
        import_doccloud_file.delay(file_pk)
        messages.success(request, "The file will be imported from DocumentCloud soon")
    return _get_redirect(request, foia)


def delete_file(request, foia):
    """Delete a file"""
    if request.user.is_staff:
        file_pk = request.POST.get("file_pk")
        FOIAFile.objects.filter(pk=file_pk).delete()
        messages.success(request, "File succesfully deleted")
    return _get_redirect(request, foia)
