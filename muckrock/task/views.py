"""
Views for the Task application
"""

# Django
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import resolve
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import FormView, TemplateView

# Standard Library
import logging
from datetime import datetime

# Third Party
import boto3
from django_filters import FilterSet

# MuckRock
from muckrock.agency.forms import AgencyForm
from muckrock.agency.models import Agency
from muckrock.agency.models.communication import AgencyAddress
from muckrock.communication.forms import AddressForm
from muckrock.communication.models import Address, PortalCommunication
from muckrock.core.views import MRFilterListView, class_view_decorator
from muckrock.foia.models import STATUS, FOIARequest
from muckrock.foia.tasks import prepare_snail_mail
from muckrock.portal.forms import PortalForm
from muckrock.task.filters import (
    FlaggedTaskFilterSet,
    NewAgencyTaskFilterSet,
    PortalTaskFilterSet,
    ResponseTaskFilterSet,
    ReviewAgencyTaskFilterSet,
    SnailMailTaskFilterSet,
    TaskFilterSet,
)
from muckrock.task.forms import (
    BulkNewAgencyTaskFormSet,
    FlaggedTaskForm,
    IncomingPortalForm,
    ProjectReviewTaskForm,
    ReplaceNewAgencyForm,
    ResponseTaskForm,
    ReviewAgencyTaskForm,
)
from muckrock.task.models import (
    CrowdfundTask,
    FlaggedTask,
    MultiRequestTask,
    NewAgencyTask,
    NewPortalTask,
    OrphanTask,
    PaymentInfoTask,
    PortalTask,
    ProjectReviewTask,
    ResponseTask,
    ReviewAgencyTask,
    SnailMailTask,
    StatusChangeTask,
    Task,
)
from muckrock.task.pdf import SnailMailPDF
from muckrock.task.tasks import snail_mail_bulk_pdf_task, submit_review_update


def count_tasks():
    """Counts all unresolved tasks and adds them to a dictionary"""
    count = (
        Task.objects.get_unresolved()
        .get_undeferred()
        .aggregate(
            all=Count("id"),
            orphan=Count("orphantask"),
            snail_mail=Count("snailmailtask"),
            review_agency=Count("reviewagencytask"),
            flagged=Count("flaggedtask"),
            projectreview=Count("projectreviewtask"),
            new_agency=Count("newagencytask"),
            response=Count("responsetask"),
            status_change=Count("statuschangetask"),
            crowdfund=Count("crowdfundtask"),
            multirequest=Count("multirequesttask"),
            portal=Count("portaltask"),
            new_portal=Count("newportaltask"),
            payment_info=Count("paymentinfotask"),
        )
    )
    return count


class TaskList(MRFilterListView):
    """List of tasks"""

    title = "Tasks"
    model = Task
    filter_class = TaskFilterSet
    template_name = "task/list.html"
    default_sort = "pk"
    bulk_actions = ["resolve"]  # bulk actions have to be lowercase and 1 word

    def get_queryset(self):
        """Apply query parameters to the queryset"""
        queryset = super(TaskList, self).get_queryset()
        task_pk = self.kwargs.get("pk")
        if task_pk:
            queryset = queryset.filter(pk=task_pk)
            if queryset.count() == 0:
                raise Http404()

        return queryset

    def get_filter(self):
        """Return an empter filter set if we are looking at a specific task"""
        if "pk" in self.kwargs:
            return FilterSet(queryset=self.get_queryset(), request=self.request)
        else:
            return super(TaskList, self).get_filter()

    def get_model(self):
        """Returns the model from the class"""
        if self.queryset is not None:
            return self.queryset.model
        if self.model is not None:
            return self.model
        raise AttributeError("No model or queryset have been defined for this view.")

    def get_context_data(self, **kwargs):
        """Adds counters for each of the sections and for processing requests."""
        context = super(TaskList, self).get_context_data(**kwargs)
        context["counters"] = count_tasks()
        context["bulk_actions"] = self.bulk_actions
        context["processing_count"] = FOIARequest.objects.filter(
            status="submitted"
        ).count()
        context["asignees"] = (
            User.objects.filter(is_staff=True)
            .select_related("profile")
            .order_by("profile__full_name")
        )
        # this is for fine-uploader
        context["settings"] = settings
        return context

    @method_decorator(user_passes_test(lambda u: u.is_staff))
    def dispatch(self, *args, **kwargs):
        """Dispatch overriden to limit access"""
        return super(TaskList, self).dispatch(*args, **kwargs)

    def get_redirect_url(self):
        """Returns the url to redirect to"""
        resolved_url = resolve(self.request.path)
        return resolved_url.url_name

    def get_tasks(self):
        """Every request should specify the task or tasks it is updating as PKs"""
        post_data = self.request.POST
        task_pks = [post_data.get("task")] + post_data.getlist("tasks")
        # clean the list of task_pks
        task_pks = [int(task_pk) for task_pk in task_pks if task_pk is not None]
        if not task_pks:
            raise ValueError("No tasks were selected, so there's nothing to do!")
        task_model = self.get_model()
        tasks = task_model.objects.filter(pk__in=task_pks)
        return tasks

    def task_post_helper(self, request, task, form_data=None):
        """Specific actions to apply to the task"""
        # pylint: disable=no-self-use
        if request.POST.get("defer"):
            date_deferred = request.POST.get("date_deferred")
            if not date_deferred:
                task.defer(None)
            else:
                try:
                    task.defer(datetime.strptime(date_deferred, "%m/%d/%Y").date())
                except ValueError:
                    pass
        elif request.POST.get("resolve"):
            task.resolve(request.user, form_data)
        return task

    def post(self, request):
        """Handle general cases for updating Task objects"""
        try:
            tasks = self.get_tasks()
            for task in tasks:
                self.task_post_helper(request, task)
        except ValueError as exception:
            if request.is_ajax():
                return HttpResponseBadRequest(exception.args[0])
            else:
                messages.warning(self.request, exception)
                return redirect(self.get_redirect_url())
        if request.is_ajax():
            return HttpResponse("OK")
        else:
            return redirect(self.get_redirect_url())


class OrphanTaskList(TaskList):
    """List view for Orphan Tasks"""

    model = OrphanTask
    title = "Orphans"
    queryset = OrphanTask.objects.preload_list()
    bulk_actions = ["reject"]

    def task_post_helper(self, request, task, form_data=None):
        """Special post helper exclusive to OrphanTasks"""
        if request.POST.get("reject"):
            blacklist = request.POST.get("blacklist", False)
            task.reject(blacklist)
            form_data = {"reject": True, "blacklist": blacklist}
            task.resolve(request.user, form_data)
        elif request.POST.get("move"):
            foia_pks = request.POST.get("foia_pks", "")
            foia_pks = foia_pks.split(", ")
            try:
                task.move(foia_pks, request.user)
                task.resolve(request.user, {"move": True, "foia_pks": foia_pks})
                messages.success(
                    request, "The communication was moved to the specified requests."
                )
            except ValueError as exception:
                messages.error(request, "Error when moving: %s" % exception)
                logging.debug("Error moving communications: %s", exception)
            except Http404:
                messages.error(request, "Tried to move to a nonexistant request.")
                logging.debug("Tried to move to a nonexistant request.")
        return super(OrphanTaskList, self).task_post_helper(request, task)


class SnailMailTaskList(TaskList):
    """List view for Snail Mail Tasks"""

    model = SnailMailTask
    filter_class = SnailMailTaskFilterSet
    title = "Snail Mails"
    queryset = SnailMailTask.objects.preload_list()

    def task_post_helper(self, request, task, form_data=None):
        """Special post helper exclusive to SnailMailTasks"""
        # we should always set the status of a request when resolving
        # a snail mail task so that the request leaves processing status
        if request.POST.get("no_mail"):
            task.resolve(request.user, {"no_mail": True})
            return task
        elif request.POST.get("lob"):
            task.resolve(request.user, {"lob": True})
            prepare_snail_mail.delay(
                task.communication.pk,
                task.category,
                task.switch,
                {"amount": task.amount},
                force=True,
            )
            return task
        elif request.POST.get("save"):
            form_data = {}
            status = request.POST.get("status")
            check_number = request.POST.get("check_number")
            if status and status not in dict(STATUS):
                messages.error(request, "Invalid status")
                return None
            try:
                if check_number:
                    check_number = int(check_number)
                    form_data["check_number"] = check_number
            except ValueError:
                messages.error(request, "Check number must be an integer")
                return None
            if status:
                task.set_status(status)
                form_data["status"] = status
            # if the task is in the payment category and we're given a check
            # number, then we should record the existence of this check
            if check_number and task.category == "p":
                task.record_check(check_number, request.user)
            task.communication.save()
            task.resolve(request.user, form_data)
        return super(SnailMailTaskList, self).task_post_helper(request, task)


class ReviewAgencyTaskList(TaskList):
    """List view for Review Agency Tasks"""

    model = ReviewAgencyTask
    filter_class = ReviewAgencyTaskFilterSet
    title = "Review Agencies"
    queryset = ReviewAgencyTask.objects.all().preload_list()

    def task_post_helper(self, request, task, form_data=None):
        """Update the requests with new contact information"""
        if request.POST.get("update"):
            form = ReviewAgencyTaskForm(
                request.POST, prefix=request.POST.get("task", "")
            )
            if form.is_valid():
                email_or_fax = form.cleaned_data["email_or_fax"]
                foia_keys = [
                    k for k in list(request.POST.keys()) if k.startswith("foias-")
                ]
                foia_pks = []
                for key in foia_keys:
                    foia_pks.extend(request.POST.getlist(key))
                foias = FOIARequest.objects.filter(pk__in=foia_pks)
                update_info = form.cleaned_data["update_agency_info"]
                snail = form.cleaned_data["snail_mail"]
                with transaction.atomic():
                    task.update_contact(email_or_fax, foias, update_info, snail)
                    # ensure th eupdated contact information is commited to the
                    # database before trying to re-submit
                    if form.cleaned_data["reply"]:
                        transaction.on_commit(
                            lambda: submit_review_update.delay(
                                foia_pks, form.cleaned_data["reply"]
                            )
                        )
                messages.success(
                    request,
                    "Updated contact information for selected requests "
                    "and sent followup message.",
                )
            else:
                messages.error(
                    request,
                    "A valid email or fax is required if " "snail mail is not checked",
                )
                return None
        return super(ReviewAgencyTaskList, self).task_post_helper(request, task)


class FlaggedTaskList(TaskList):
    """List view for Flagged Tasks"""

    model = FlaggedTask
    filter_class = FlaggedTaskFilterSet
    title = "Flagged"
    queryset = FlaggedTask.objects.preload_list()

    def task_post_helper(self, request, task, form_data=None):
        """Special post handler for FlaggedTasks"""
        form_data = {}
        if request.POST.get("reply"):
            form_data["reply"] = True
            reply_form = FlaggedTaskForm(request.POST)
            if reply_form.is_valid() and task.user:
                text = reply_form.cleaned_data["text"]
                task.reply(text)
                form_data["text"] = text
            elif reply_form.is_valid():
                messages.error(request, "Cannot reply - task has no user")
                return None
            else:
                messages.error(request, "The form is invalid")
                return None
        return super(FlaggedTaskList, self).task_post_helper(
            request, task, form_data=form_data
        )


class ProjectReviewTaskList(TaskList):
    """List view for Project Review Tasks"""

    model = ProjectReviewTask
    title = "Pending Projects"
    queryset = ProjectReviewTask.objects.preload_list()

    def task_post_helper(self, request, task, form_data=None):
        """Special post handler for ProjectReviewTasks"""
        form = ProjectReviewTaskForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data["reply"]
            action = request.POST.get("action", None)
            if action == "reply":
                task.reply(text)
            elif action == "approve":
                task.approve(text)
                task.resolve(request.user, {"action": "approve"})
            elif action == "reject":
                task.reject(text)
                task.resolve(request.user, {"action": "reject"})
        return super(ProjectReviewTaskList, self).task_post_helper(request, task)


class NewAgencyTaskList(TaskList):
    """List view for New Agency Tasks"""

    title = "New Agencies"
    filter_class = NewAgencyTaskFilterSet
    queryset = NewAgencyTask.objects.preload_list()

    def task_post_helper(self, request, task, form_data=None):
        """Special post handlers exclusive to NewAgencyTasks"""
        if request.POST.get("approve"):
            new_agency_form = AgencyForm(
                request.POST, instance=task.agency, prefix=request.POST.get("task", "")
            )
            if new_agency_form.is_valid():
                new_agency_form.save()
            else:
                raise ValueError("The agency info form is invalid.")
            task.approve()
            form_data = new_agency_form.cleaned_data
            # phone numbers must be strings not phone number objects to serialize
            if form_data.get("phone"):
                form_data["phone"] = str(form_data["phone"])
            if form_data.get("fax"):
                form_data["fax"] = str(form_data["fax"])
            if form_data.get("jurisdiction"):
                form_data["jurisdiction"] = form_data["jurisdiction"].pk
            form_data.update({"approve": True})
            task.resolve(request.user, form_data)
        elif request.POST.get("replace"):
            form = ReplaceNewAgencyForm(
                request.POST, prefix=request.POST.get("task", "")
            )
            if form.is_valid():
                replace_agency = form.cleaned_data["replace_agency"]
                task.reject(replace_agency)
                form_data = {"replace": True, "replace_agency": replace_agency.pk}
                task.resolve(request.user, form_data)
            else:
                messages.error(request, "Bad form data")
                return None
        elif request.POST.get("reject"):
            task.reject()
            form_data = {"reject": True}
            task.resolve(request.user, form_data)
        elif request.POST.get("spam"):
            task.spam(request.user)
            form_data = {"spam": True}
            task.resolve(request.user, form_data)
        return super(NewAgencyTaskList, self).task_post_helper(request, task)


class ResponseTaskList(TaskList):
    """List view for Response Tasks"""

    title = "Responses"
    filter_class = ResponseTaskFilterSet
    queryset = ResponseTask.objects.preload_list()

    def task_post_helper(self, request, task, form_data=None):
        """Special post helper exclusive to ResponseTask"""
        if request.POST.get("proxy") or request.POST.get("save"):
            form = ResponseTaskForm(request.POST, task=task)
            if not form.is_valid():
                messages.error(request, "Form is invalid")
                return None
            action_taken, error_msgs = form.process_form(task, request.user)
            for msg in error_msgs:
                messages.error(request, msg)
            if action_taken and not error_msgs:
                form_data = form.cleaned_data
                if form_data["price"] is not None:
                    # cast from decimal to float, since decimal
                    # is not json serializable
                    form_data["price"] = float(form_data["price"])
                if form_data.get("date_estimate"):
                    # to string for json
                    form_data["date_estimate"] = form_data["date_estimate"].isoformat()
                if task.scan:
                    task.communication.hidden = False
                    task.communication.create_agency_notifications()
                    task.communication.save()
                task.resolve(request.user, form.cleaned_data)
        return super(ResponseTaskList, self).task_post_helper(request, task)


class StatusChangeTaskList(TaskList):
    """List view for Status Change Tasks"""

    title = "Status Change"
    queryset = StatusChangeTask.objects.preload_list()


class CrowdfundTaskList(TaskList):
    """List view for Crowdfund Tasks"""

    title = "Crowdfunds"
    queryset = CrowdfundTask.objects.preload_list()


class MultiRequestTaskList(TaskList):
    """List view for MultiRequest Tasks"""

    title = "Multi-Requests"
    queryset = MultiRequestTask.objects.preload_list()

    def task_post_helper(self, request, task, form_data=None):
        """Special post helper exclusive to MultiRequestTasks"""
        if request.POST.get("action") == "submit":
            agency_list = request.POST.getlist("agencies")
            task.submit(agency_list)
            task.resolve(request.user, {"action": "submit", "agencies": agency_list})
            messages.success(request, "Multirequest submitted")
        elif request.POST.get("action") == "reject":
            task.reject()
            task.resolve(request.user, {"action": "reject"})
            messages.error(request, "Multirequest rejected")
        return super(MultiRequestTaskList, self).task_post_helper(request, task)


class PortalTaskList(TaskList):
    """List view for Portal Tasks"""

    title = "Portal"
    filter_class = PortalTaskFilterSet
    queryset = PortalTask.objects.preload_list()

    def task_post_helper(self, request, task, form_data=None):
        """Special post helper exclusive to Portal Tasks"""
        # incoming and outgoing portal tasks are very different
        # incoming are very similar to response tasks
        # outgoing are very similar to snail mail tasks
        if request.POST.get("save"):
            if task.category == "i":
                self._incoming_handler(request, task)
            else:
                self._outgoing_handler(request, task)
        elif request.POST.get("reject"):
            task.resolve(request.user, {"reject": "true"})
        return super(PortalTaskList, self).task_post_helper(request, task)

    def _incoming_handler(self, request, task):
        """POST handler for incoming portal tasks"""
        # pylint: disable=no-self-use
        form = IncomingPortalForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Form is invalid")
            return
        action_taken, error_msgs = form.process_form(task, request.user)
        for msg in error_msgs:
            messages.error(request, msg)
        new_text = form.cleaned_data.get("communication")
        keep_hidden = form.cleaned_data.get("keep_hidden")
        password = form.cleaned_data.get("word_to_pass")
        if new_text:
            task.communication.communication = new_text
        if not keep_hidden:
            task.communication.hidden = False
            task.communication.create_agency_notifications()
        if password:
            task.communication.foia.portal_password = password
            task.communication.foia.save()
        task.communication.save()
        if task.communication.foia.portal:
            # If a communication is incorrectly sent to a request with a portal
            # it may be moved to a request without a portal - do not save a
            # portal communication in this case
            PortalCommunication.objects.create(
                communication=task.communication,
                sent_datetime=timezone.now(),
                portal=task.communication.foia.portal,
                direction="incoming",
            )
        if action_taken and not error_msgs:
            form_data = form.cleaned_data
            if form_data["price"] is not None:
                # cast from decimal to float, since decimal
                # is not json serializable
                form_data["price"] = float(form_data["price"])
            if form_data.get("date_estimate"):
                # to string for json
                form_data["date_estimate"] = form_data["date_estimate"].isoformat()
            task.resolve(request.user, form_data)

    def _outgoing_handler(self, request, task):
        """POST handler for outgoing portal tasks"""
        # pylint: disable=no-self-use
        status = request.POST.get("status")
        if status and status not in dict(STATUS):
            messages.error(request, "Invalid status")
            return
        password = request.POST.get("word_to_pass", "")
        tracking_number = request.POST.get("tracking_number")
        foia = task.communication.foia
        if len(password) > 20:
            messages.error(request, "Password cannot be longer than 20 characters")
            return
        if status:
            task.set_status(status)
        save = False
        if tracking_number:
            foia.add_tracking_id(tracking_number[:255])
            save = True
        if not foia.portal_password and password:
            foia.portal_password = password
            save = True
        if save:
            foia.save()
        if task.communication.foia.agency.portal:
            PortalCommunication.objects.create(
                communication=task.communication,
                sent_datetime=timezone.now(),
                portal=task.communication.foia.agency.portal,
                direction="outgoing",
            )
        form_data = {
            "status": status,
            "word_to_pass": password,
            "tracking_number": tracking_number,
        }
        task.resolve(request.user, form_data)


class NewPortalTaskList(TaskList):
    """List view for New Portal Tasks"""

    title = "New Portal"
    queryset = NewPortalTask.objects.preload_list()

    def task_post_helper(self, request, task, form_data=None):
        """Special post helper exclusive to New Portal Tasks"""
        if request.POST.get("approve"):
            foia = task.communication.foia
            form = PortalForm(request.POST, foia=foia)
            if not form.is_valid():
                raise ValueError(form.errors)
            form.save()
            # save the portal to the agency as well
            foia.agency.portal = foia.portal
            foia.agency.save()
            form_data = form.cleaned_data
            if form_data.get("portal"):
                form_data["portal"] = form_data["portal"].pk
            task.resolve(request.user, form_data)
        elif request.POST.get("reject"):
            task.resolve(request.user, {"reject": "true"})
            messages.error(request, "New portal rejected")
        return super(NewPortalTaskList, self).task_post_helper(request, task)


class PaymentInfoTaskList(TaskList):
    """List view for Payment Info Tasks"""

    model = PaymentInfoTask
    title = "Payment Info"
    queryset = PaymentInfoTask.objects.preload_list()

    @transaction.atomic
    def task_post_helper(self, request, task, form_data=None):
        if request.POST.get("save"):
            agency = task.communication.foia.agency
            form = AddressForm(request.POST, agency=agency)
            if not form.is_valid():
                raise ValueError(form.errors)
            if agency.get_addresses("check").exists():
                raise ValueError("This agency already has a check address")
            address, _created = Address.objects.get_or_create(
                # set address override to blank for uniqueness purposes
                address="",
                **form.cleaned_data,
            )
            AgencyAddress.objects.create(
                agency=agency, address=address, request_type="check"
            )
            tasks = PaymentInfoTask.objects.filter(
                resolved=False, communication__foia__agency=agency
            )
            for task_ in tasks:
                # send the check
                task_.resolve(request.user, form.cleaned_data)
                transaction.on_commit(
                    lambda t=task_: prepare_snail_mail.delay(
                        t.communication.pk, "p", False, {"amount": t.amount}
                    )
                )
        elif request.POST.get("reject"):
            SnailMailTask.objects.create(
                category="p",
                communication=task.communication,
                user=task.communication.from_user,
                reason="pay",
                amount=task.amount,
            )
            task.resolve(request.user, {"reject": "true"})
            messages.error(request, "Payment info task rejected")
        return super(PaymentInfoTaskList, self).task_post_helper(request, task)


class RequestTaskList(TemplateView):
    """Displays all the tasks for a given request."""

    title = "Request Tasks"
    template_name = "lists/request_task_list.html"

    def get_queryset(self):
        """Get tasks with related bjects preloaded"""
        # pylint: disable=attribute-defined-outside-init
        # pylint: disable=unsubscriptable-object
        self.foia_request = get_object_or_404(
            FOIARequest.objects.select_related(
                "agency__jurisdiction__parent__parent", "composer__user__profile"
            ),
            pk=self.kwargs["pk"],
        )
        user = self.request.user
        tasks = Task.objects.filter_by_foia(self.foia_request, user)
        return tasks

    def get_context_data(self, **kwargs):
        # pylint: disable=bad-super-call
        # we purposely call super on TaskList here, as we do want the generic
        # list views method to be called, but we don't need any of the
        # data calculated in the TaskList method, so using it just slows us down
        context = super(RequestTaskList, self).get_context_data(**kwargs)
        context["title"] = self.title
        context["object_list"] = self.get_queryset()
        context["foia"] = self.foia_request
        context["foia_url"] = self.foia_request.get_absolute_url()
        return context


@user_passes_test(lambda u: u.is_staff)
def snail_mail_bulk_pdf(request):
    """Generate the task asynchrnously"""
    # pylint: disable=unused-argument
    pdf_name = timezone.now().strftime("snail_mail_pdfs/%Y/%m/%d/%H-%M-%S.pdf")
    snail_mail_bulk_pdf_task.delay(pdf_name, request.GET.dict())

    # Generate GET/HEAD presigned URLs for the client
    urls = {}
    s3 = boto3.client("s3")
    for action in ["head", "get"]:
        urls[f"{action}_url"] = s3.generate_presigned_url(
            ClientMethod=f"{action}_object",
            Params={"Bucket": settings.AWS_MEDIA_BUCKET_NAME, "Key": pdf_name},
            ExpiresIn=3600,
        )

    return JsonResponse(urls)


@user_passes_test(lambda u: u.is_staff)
def snail_mail_pdf(request, pk):
    """Return a PDF file for a snail mail request"""
    # pylint: disable=unused-argument
    snail = get_object_or_404(SnailMailTask.objects.preload_pdf(), pk=pk)

    # generate the pdf and merge all pdf attachments
    pdf = SnailMailPDF(snail.communication, snail.category, snail.switch, snail.amount)
    prepared_pdf, _page_count, _files, _mail = pdf.prepare()

    if prepared_pdf is None:
        return render(
            request, "error.html", {"message": "There was an error processing this PDF"}
        )

    # return as a response
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'filename="{}.pdf"'.format(snail.communication.pk)
    response.write(prepared_pdf.read())
    return response


@user_passes_test(lambda u: u.is_staff)
def assign_to(request):
    """Assign a task to a user"""
    try:
        task_pk = int(request.POST.get("task_pk"))
        asignee_pk = int(request.POST.get("asignee"))
    except ValueError:
        return HttpResponseForbidden
    task = get_object_or_404(Task, pk=task_pk)
    if asignee_pk == 0:
        task.assigned = None
    else:
        task.assigned = get_object_or_404(User, pk=asignee_pk)
    task.save()
    return HttpResponse("OK")


@user_passes_test(lambda u: u.is_staff)
def review_agency_ajax(request, pk):
    """Render a single review agency task"""
    task = get_object_or_404(ReviewAgencyTask, pk=pk)
    context = {}
    context["task"] = task
    context["emails"] = task.agency.agencyemail_set.all()
    context["faxes"] = task.agency.agencyphone_set.filter(phone__type="fax")
    context["phones"] = task.agency.agencyphone_set.filter(phone__type="phone")
    context["addresses"] = task.agency.agencyaddress_set.all()
    context["num_open_requests"] = task.agency.foiarequest_set.get_open().count()
    latest_response = task.latest_response()
    if latest_response:
        context["latest_response"] = (
            latest_response,
            (timezone.now() - latest_response).days,
        )
    context["review_data"] = task.get_review_data()
    return render(request, "lib/review_agency.html", context)


@class_view_decorator(user_passes_test(lambda u: u.is_staff))
class BulkNewAgency(FormView):
    """Allow bulk creation of new agencies"""

    template_name = "task/bulk_new_agency.html"
    form_class = BulkNewAgencyTaskFormSet

    def get_context_data(self, **kwargs):
        """Name the form formset"""
        context = super(BulkNewAgency, self).get_context_data(**kwargs)
        formset = context.pop("form")
        context["formset"] = formset
        return context

    def form_valid(self, form):
        """Create the agencies"""
        for form_ in form.forms:
            name = form_.cleaned_data.get("name")
            jurisdiction = form_.cleaned_data.get("jurisdiction")
            if name and jurisdiction:
                Agency.objects.create_new(name, jurisdiction, self.request.user)
        messages.success(self.request, "Successfully create new agencies")
        return redirect("new-agency-task-list")
