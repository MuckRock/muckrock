"""
Views for the Task application
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.files.base import ContentFile
from django.core.urlresolvers import resolve
from django.db import transaction
from django.db.models import Count
from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

import logging
from datetime import datetime
from django_filters import FilterSet
from PyPDF2 import PdfFileMerger
from cStringIO import StringIO

from muckrock.agency.forms import AgencyForm
from muckrock.agency.models import Agency
from muckrock.communication.models import (
        EmailAddress,
        MailCommunication,
        PortalCommunication,
        )
from muckrock.foia.models import STATUS, FOIARequest
from muckrock.task.filters import (
    TaskFilterSet,
    ResponseTaskFilterSet,
    NewAgencyTaskFilterSet,
    SnailMailTaskFilterSet,
    FlaggedTaskFilterSet,
    StaleAgencyTaskFilterSet,
    ReviewAgencyTaskFilterSet,
    PortalTaskFilterSet,
)
from muckrock.task.forms import (
    FlaggedTaskForm,
    StaleAgencyTaskForm,
    ResponseTaskForm,
    ProjectReviewTaskForm,
    ReviewAgencyTaskForm,
    )
from muckrock.task.models import (
    Task,
    OrphanTask,
    SnailMailTask,
    StaleAgencyTask,
    ReviewAgencyTask,
    FlaggedTask,
    NewAgencyTask,
    ResponseTask,
    CrowdfundTask,
    MultiRequestTask,
    StatusChangeTask,
    ProjectReviewTask,
    NewExemptionTask,
    PortalTask,
    )
from muckrock.task.tasks import submit_review_update, snail_mail_bulk_pdf_task
from muckrock.task.pdf import SnailMailPDF
from muckrock.views import MRFilterListView

# pylint:disable=missing-docstring

def count_tasks():
    """Counts all unresolved tasks and adds them to a dictionary"""
    count = Task.objects.filter(resolved=False).aggregate(
        all=Count('id'),
        orphan=Count('orphantask'),
        snail_mail=Count('snailmailtask'),
        stale_agency=Count('staleagencytask'),
        review_agency=Count('reviewagencytask'),
        flagged=Count('flaggedtask'),
        projectreview=Count('projectreviewtask'),
        new_agency=Count('newagencytask'),
        response=Count('responsetask'),
        status_change=Count('statuschangetask'),
        crowdfund=Count('crowdfundtask'),
        multirequest=Count('multirequesttask'),
        new_exemption=Count('newexemptiontask'),
        portal=Count('portaltask'),
        )
    return count


class TaskList(MRFilterListView):
    """List of tasks"""
    title = 'Tasks'
    model = Task
    filter_class = TaskFilterSet
    template_name = 'task/list.html'
    default_sort = 'pk'
    bulk_actions = ['resolve'] # bulk actions have to be lowercase and 1 word

    def get_queryset(self):
        """Apply query parameters to the queryset"""
        queryset = super(TaskList, self).get_queryset()
        task_pk = self.kwargs.get('pk')
        if task_pk:
            # when we are looking for a specific task,
            # we filter the queryset for that task's pk
            # and override show_resolved and resolved_by
            queryset = queryset.filter(pk=task_pk)
            if queryset.count() == 0:
                raise Http404()
        return queryset

    def get_filter(self):
        """Return an empter filter set if we are looking at a specific task"""
        if 'pk' in self.kwargs:
            return FilterSet(queryset=self.get_queryset(), request=self.request)
        else:
            return super(TaskList, self).get_filter()

    def get_model(self):
        """Returns the model from the class"""
        if self.queryset is not None:
            return self.queryset.model
        if self.model is not None:
            return self.model
        raise AttributeError('No model or queryset have been defined for this view.')

    def get_context_data(self, **kwargs):
        """Adds counters for each of the sections and for processing requests."""
        context = super(TaskList, self).get_context_data(**kwargs)
        context['counters'] = count_tasks()
        context['bulk_actions'] = self.bulk_actions
        context['processing_count'] = FOIARequest.objects.filter(status='submitted').count()
        # These are for fine-uploader
        context['MAX_ATTACHMENT_NUM'] = settings.MAX_ATTACHMENT_NUM
        context['MAX_ATTACHMENT_SIZE'] = settings.MAX_ATTACHMENT_SIZE
        context['ALLOWED_FILE_MIMES'] = settings.ALLOWED_FILE_MIMES
        context['ALLOWED_FILE_EXTS'] = settings.ALLOWED_FILE_EXTS
        context['AWS_STORAGE_BUCKET_NAME'] = settings.AWS_STORAGE_BUCKET_NAME
        context['AWS_ACCESS_KEY_ID'] = settings.AWS_ACCESS_KEY_ID
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
        task_pks = [post_data.get('task')] + post_data.getlist('tasks')
        # clean the list of task_pks
        task_pks = [int(task_pk) for task_pk in task_pks if task_pk is not None]
        if not task_pks:
            raise ValueError('No tasks were selected, so there\'s nothing to do!')
        task_model = self.get_model()
        tasks = task_model.objects.filter(pk__in=task_pks)
        return tasks

    def task_post_helper(self, request, task):
        """Specific actions to apply to the task"""
        # pylint: disable=no-self-use
        if request.POST.get('resolve'):
            task.resolve(request.user)
        return task

    def post(self, request):
        """Handle general cases for updating Task objects"""
        try:
            tasks = self.get_tasks()
        except ValueError as exception:
            if request.is_ajax():
                return HttpResponse(400)
            else:
                messages.warning(self.request, exception)
                return redirect(self.get_redirect_url())
        for task in tasks:
            self.task_post_helper(request, task)
        if request.is_ajax():
            return HttpResponse(200)
        else:
            return redirect(self.get_redirect_url())


class OrphanTaskList(TaskList):
    model = OrphanTask
    title = 'Orphans'
    queryset = OrphanTask.objects.preload_list()
    bulk_actions = ['reject']

    def task_post_helper(self, request, task):
        """Special post helper exclusive to OrphanTasks"""
        if request.POST.get('reject'):
            blacklist = request.POST.get('blacklist', False)
            task.reject(blacklist)
            task.resolve(request.user)
        elif request.POST.get('move'):
            foia_pks = request.POST.get('move', '')
            foia_pks = foia_pks.split(', ')
            try:
                task.move(foia_pks)
                task.resolve(request.user)
                messages.success(request, 'The communication was moved to the specified requests.')
            except ValueError as exception:
                messages.error(request, 'Error when moving: %s' % exception)
                logging.debug('Error moving communications: %s', exception)
            except Http404:
                messages.error(request, 'Tried to move to a nonexistant request.')
                logging.debug('Tried to move to a nonexistant request.')
        return super(OrphanTaskList, self).task_post_helper(request, task)


class SnailMailTaskList(TaskList):
    model = SnailMailTask
    filter_class = SnailMailTaskFilterSet
    title = 'Snail Mails'
    queryset = SnailMailTask.objects.preload_list()

    def task_post_helper(self, request, task):
        """Special post helper exclusive to SnailMailTasks"""
        # we should always set the status of a request when resolving
        # a snail mail task so that the request leaves processing status
        status = request.POST.get('status')
        check_number = request.POST.get('check_number')
        if status and status not in dict(STATUS):
            messages.error(request, 'Invalid status')
            return
        try:
            if check_number:
                check_number = int(check_number)
        except ValueError:
            messages.error(request, 'Check number must be an integer')
            return
        if status:
            task.set_status(status)
        # if the task is in the payment category and we're given a check
        # number, then we should record the existence of this check
        if check_number and task.category == 'p':
            task.record_check(check_number, request.user)
        # ensure a mail communication is created
        # it should have been already created when the PDF was generated
        MailCommunication.objects.get_or_create(
                communication=task.communication,
                defaults={
                    'to_address': task.communication.foia.address,
                    'sent_datetime': datetime.now(),
                    }
                )
        task.communication.save()
        task.resolve(request.user)
        return super(SnailMailTaskList, self).task_post_helper(request, task)


class StaleAgencyTaskList(TaskList):
    model = StaleAgencyTask
    filter_class = StaleAgencyTaskFilterSet
    title = 'Stale Agencies'
    queryset = StaleAgencyTask.objects.preload_list()

    def task_post_helper(self, request, task):
        """Check the new email is valid and, if so, apply it"""
        if request.POST.get('update'):
            email_form = StaleAgencyTaskForm(request.POST)
            if email_form.is_valid():
                new_email = EmailAddress.objects.fetch(
                        email_form.cleaned_data['email'])
                foia_pks = request.POST.getlist('foia')
                foias = FOIARequest.objects.filter(pk__in=foia_pks)
                task.update_email(new_email, foias)
            else:
                messages.error(request, 'The email is invalid.')
                return
        return super(StaleAgencyTaskList, self).task_post_helper(request, task)


class ReviewAgencyTaskList(TaskList):
    model = ReviewAgencyTask
    filter_class = ReviewAgencyTaskFilterSet
    title = 'Review Agencies'
    queryset = ReviewAgencyTask.objects.all().preload_list()

    def task_post_helper(self, request, task):
        """Update the requests with new contact information"""
        if request.POST.get('update'):
            form = ReviewAgencyTaskForm(request.POST)
            if form.is_valid():
                email_or_fax = form.cleaned_data['email_or_fax']
                foia_keys = [k for k in request.POST.keys()
                        if k.startswith('foias-')]
                foia_pks = []
                for key in foia_keys:
                    foia_pks.extend(request.POST.getlist(key))
                foias = FOIARequest.objects.filter(pk__in=foia_pks)
                update_info = form.cleaned_data['update_agency_info']
                snail = form.cleaned_data['snail_mail']
                task.agency.unmark_stale()
                with transaction.atomic():
                    task.update_contact(email_or_fax, foias, update_info, snail)
                    # ensure th eupdated contact information is commited to the
                    # database before trying to re-submit
                    if form.cleaned_data['reply']:
                        transaction.on_commit(
                                lambda: submit_review_update.delay(
                                    foia_pks,
                                    form.cleaned_data['reply'],
                                    ))
                messages.success(
                        request,
                        'Updated contact information for selected requests '
                        'and sent followup message.',
                        )
            else:
                messages.error(
                        request,
                        'A valid email or fax is required if '
                        'snail mail is not checked',
                        )
                return
        return super(ReviewAgencyTaskList, self).task_post_helper(request, task)


class FlaggedTaskList(TaskList):
    model = FlaggedTask
    filter_class = FlaggedTaskFilterSet
    title = 'Flagged'
    queryset = FlaggedTask.objects.preload_list()

    def task_post_helper(self, request, task):
        """Special post handler for FlaggedTasks"""
        if request.POST.get('reply'):
            reply_form = FlaggedTaskForm(request.POST)
            if reply_form.is_valid() and task.user:
                text = reply_form.cleaned_data['text']
                task.reply(text)
            elif reply_form.is_valid():
                messages.error(request, 'Cannot reply - task has no user')
                return
            else:
                messages.error(request, 'The form is invalid')
                return
        if request.POST.get('resolve'):
            task.resolve(request.user)
        return super(FlaggedTaskList, self).task_post_helper(request, task)


class ProjectReviewTaskList(TaskList):
    model = ProjectReviewTask
    title = 'Pending Projects'
    queryset = ProjectReviewTask.objects.preload_list()

    def task_post_helper(self, request, task):
        """Special post handler for ProjectReviewTasks"""
        form = ProjectReviewTaskForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data['reply']
            action = request.POST.get('action', None)
            if action == 'reply':
                task.reply(text)
            elif action == 'approve':
                task.approve(text)
                task.resolve(request.user)
            elif action == 'reject':
                task.reject(text)
                task.resolve(request.user)
        return super(ProjectReviewTaskList, self).task_post_helper(request, task)


class NewAgencyTaskList(TaskList):
    title = 'New Agencies'
    filter_class = NewAgencyTaskFilterSet
    queryset = NewAgencyTask.objects.preload_list()

    def task_post_helper(self, request, task):
        """Special post handlers exclusive to NewAgencyTasks"""
        if request.POST.get('approve'):
            new_agency_form = AgencyForm(request.POST, instance=task.agency)
            if new_agency_form.is_valid():
                new_agency_form.save()
            else:
                messages.error(request, 'The agency info form is invalid.')
                return
            task.approve()
            task.resolve(request.user)
        if request.POST.get('reject'):
            replacement_agency_id = request.POST.get('replacement')
            replacement_agency = get_object_or_404(Agency, id=replacement_agency_id)
            if replacement_agency.status != 'approved':
                messages.error(
                        request,
                        'Replacement agency must be an "approved" agency.',
                        )
                return
            task.reject(replacement_agency)
            task.resolve(request.user)
        return super(NewAgencyTaskList, self).task_post_helper(request, task)


class ResponseTaskList(TaskList):
    title = 'Responses'
    filter_class = ResponseTaskFilterSet
    queryset = ResponseTask.objects.preload_list()

    def task_post_helper(self, request, task):
        """Special post helper exclusive to ResponseTask"""
        task = super(ResponseTaskList, self).task_post_helper(request, task)
        form = ResponseTaskForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Form is invalid')
            return
        action_taken, error_msgs = form.process_form(task)
        for msg in error_msgs:
            messages.error(request, msg)
        if action_taken and not error_msgs:
            task.resolve(request.user)


class StatusChangeTaskList(TaskList):
    title = 'Status Change'
    queryset = StatusChangeTask.objects.preload_list()


class CrowdfundTaskList(TaskList):
    title = 'Crowdfunds'
    queryset = CrowdfundTask.objects.preload_list()


class MultiRequestTaskList(TaskList):
    title = 'Multi-Requests'
    queryset = MultiRequestTask.objects.preload_list()

    def task_post_helper(self, request, task):
        """Special post helper exclusive to MultiRequestTasks"""
        if request.POST.get('action') == 'submit':
            agency_list = request.POST.getlist('agencies')
            task.submit(agency_list)
            task.resolve(request.user)
            messages.success(request, 'Multirequest submitted')
        elif request.POST.get('action') == 'reject':
            task.reject()
            task.resolve(request.user)
            messages.error(request, 'Multirequest rejected')
        return super(MultiRequestTaskList, self).task_post_helper(request, task)


class NewExemptionTaskList(TaskList):
    title = 'New Exemptions'
    queryset = NewExemptionTask.objects.preload_list()


class PortalTaskList(TaskList):
    title = 'Portal'
    filter_class = PortalTaskFilterSet
    queryset = PortalTask.objects.preload_list()

    def task_post_helper(self, request, task):
        """Special post helper exclusive to Portal Tasks"""
        # incoming and outgoing portal tasks are very different
        # incoming are very similar to response tasks
        # outgoing are very similar to snail mail tasks
        if task.category == 'i':
            self._incoming_handler(request, task)
        else:
            self._outgoing_handler(request, task)
        return task

    def _incoming_handler(self, request, task):
        """POST handler for incoming portal tasks"""
        # pylint: disable=no-self-use
        form = ResponseTaskForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Form is invalid')
            return
        action_taken, error_msgs = form.process_form(task)
        for msg in error_msgs:
            messages.error(request, msg)
        new_text = request.POST.get('communication')
        keep_hidden = request.POST.get('keep_hidden')
        if new_text:
            task.communication.communication = new_text
        if not keep_hidden:
            task.communication.hidden = False
            task.communication.create_agency_notifications()
        task.communication.save()
        PortalCommunication.objects.create(
                communication=task.communication,
                sent_datetime=datetime.now(),
                portal=task.communication.foia.portal,
                direction='incoming',
                )
        if action_taken and not error_msgs:
            task.resolve(request.user)

    def _outgoing_handler(self, request, task):
        """POST handler for outgoing portal tasks"""
        # pylint: disable=no-self-use
        status = request.POST.get('status')
        if status and status not in dict(STATUS):
            messages.error(request, 'Invalid status')
            return
        password = request.POST.get('word_to_pass')
        tracking_number = request.POST.get('tracking_number')
        foia = task.communication.foia
        if len(password) > 20:
            messages.error(
                    request,
                    'Password cannot be longer than 20 characters',
                    )
            return
        if status:
            task.set_status(status)
        save = False
        if tracking_number:
            foia.tracking_id = tracking_number[:255]
            save = True
        if not foia.portal_password and password:
            foia.portal_password = password
            save = True
        if save:
            foia.save()
        PortalCommunication.objects.create(
                communication=task.communication,
                sent_datetime=datetime.now(),
                portal=task.communication.foia.portal,
                direction='outgoing',
                )
        task.resolve(request.user)


class RequestTaskList(TemplateView):
    """Displays all the tasks for a given request."""
    title = 'Request Tasks'
    template_name = 'lists/request_task_list.html'

    def get_queryset(self):
        # pylint: disable=attribute-defined-outside-init
        # pylint: disable=unsubscriptable-object
        self.foia_request = get_object_or_404(
                FOIARequest.objects.select_related(
                    'agency__jurisdiction',
                    'jurisdiction__parent__parent',
                    'user__profile'),
                pk=self.kwargs['pk'])
        user = self.request.user
        tasks = Task.objects.filter_by_foia(self.foia_request, user)
        return tasks

    def get_context_data(self, **kwargs):
        # pylint: disable=bad-super-call
        # we purposely call super on TaskList here, as we do want the generic
        # list views method to be called, but we don't need any of the
        # data calculated in the TaskList method, so using it just slows us down
        context = super(RequestTaskList, self).get_context_data(**kwargs)
        context['title'] = self.title
        context['object_list'] = self.get_queryset()
        context['foia'] = self.foia_request
        context['foia_url'] = self.foia_request.get_absolute_url()
        return context


@user_passes_test(lambda u: u.is_staff)
def snail_mail_bulk_pdf(request):
    """Generate the task asynchrnously"""
    # pylint: disable=unused-argument
    pdf_name = datetime.now().strftime('snail_mail_pdfs/%Y/%m/%d/%H-%M-%S.pdf')
    snail_mail_bulk_pdf_task.delay(pdf_name)
    return JsonResponse({'pdf_name': pdf_name})


@user_passes_test(lambda u: u.is_staff)
def snail_mail_pdf(request, pk):
    """Return a PDF file for a snail mail request"""
    # pylint: disable=unused-argument
    snail = get_object_or_404(SnailMailTask.objects.preload_pdf(), pk=pk)
    merger = PdfFileMerger()

    # generate the pdf and merge all pdf attachments
    pdf = SnailMailPDF(snail.communication.foia)
    pdf.generate()
    merger.append(StringIO(pdf.output(dest='S')))
    for file_ in snail.communication.files.all():
        if file_.get_extension() == 'pdf':
            merger.append(file_.ffile)
    output = StringIO()
    merger.write(output)

    # attach to the mail communication
    mail, _ = MailCommunication.objects.update_or_create(
            communication=snail.communication,
            defaults={
                'to_address': snail.communication.foia.address,
                'sent_datetime': datetime.now(),
                }
            )
    output.seek(0)
    mail.pdf.save(
            '{}.pdf'.format(snail.communication.pk),
            ContentFile(output.read()),
            )

    # return as a response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
            'filename="{}.pdf"'.format(snail.communication.pk))
    output.seek(0)
    response.write(output.read())
    return response
