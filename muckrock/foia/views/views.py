"""
Views for the FOIA application
"""

from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template.defaultfilters import slugify
from django.template import RequestContext
from django.views.generic.detail import DetailView

import actstream
from datetime import datetime
import json
import logging

from muckrock.foia.codes import CODES
from muckrock.foia.forms import \
    RequestFilterForm, \
    FOIAEmbargoForm, \
    FOIANoteForm, \
    FOIAEstimatedCompletionDateForm, \
    FOIAAccessForm
from muckrock.foia.models import \
    FOIARequest, \
    FOIAMultiRequest, \
    STATUS, END_STATUS
from muckrock.foia.views.composers import get_foia
from muckrock.foia.views.comms import move_comm,\
                                      delete_comm,\
                                      save_foia_comm,\
                                      resend_comm,\
                                      change_comm_status
from muckrock.qanda.models import Question
from muckrock.settings import STRIPE_PUB_KEY
from muckrock.tags.models import Tag
from muckrock.task.models import Task, FlaggedTask, StatusChangeTask
from muckrock.views import class_view_decorator, MRFilterableListView

# pylint: disable=too-many-ancestors

logger = logging.getLogger(__name__)
STATUS_NODRAFT = [st for st in STATUS if st != ('started', 'Draft')]


class RequestList(MRFilterableListView):
    """Base list view for other list views to inherit from"""
    model = FOIARequest
    title = 'Requests'
    template_name = 'lists/request_list.html'
    default_sort = 'title'

    def get_filters(self):
        """Adds request-specific filter fields"""
        base_filters = super(RequestList, self).get_filters()
        new_filters = [{'field': 'status', 'lookup': 'exact'}]
        return base_filters + new_filters

    def get_context_data(self, **kwargs):
        """Changes filter_form to use RequestFilterForm instead of the default"""
        context = super(RequestList, self).get_context_data(**kwargs)
        filter_data = self.get_filter_data()
        context['filter_form'] = RequestFilterForm(initial=filter_data['filter_initials'])
        return context

    def get_queryset(self):
        """Limits requests to those visible by current user"""
        objects = super(RequestList, self).get_queryset()
        objects = objects.select_related('jurisdiction')
        objects = objects.only(
                'title', 'slug', 'status', 'date_submitted',
                'date_due', 'date_updated', 'jurisdiction__slug')
        return objects.get_viewable(self.request.user)


@class_view_decorator(login_required)
class MyRequestList(RequestList):
    """View requests owned by current user"""
    template_name = 'lists/request_my_list.html'

    def post(self, request):
        """Handle updating read status"""
        try:
            post = request.POST
            foia_pks = post.getlist('foia')
            if post.get('submit') == 'Mark as Read':
                FOIARequest.objects.filter(pk__in=foia_pks).update(updated=False)
            elif post.get('submit') == 'Mark as Unread':
                FOIARequest.objects.filter(pk__in=foia_pks).update(updated=True)
            elif post.get('submit') == 'Mark All as Read':
                FOIARequest.objects.filter(user=self.request.user, updated=True)\
                                   .update(updated=False)
        except FOIARequest.DoesNotExist:
            pass
        return redirect('foia-mylist')

    def get_filters(self):
        """Removes the 'users' filter, because its _my_ requests"""
        filters = super(MyRequestList, self).get_filters()
        for filter_dict in filters:
            if 'user' in filter_dict.values():
                filters.pop(filters.index(filter_dict))
        return filters

    def get_queryset(self):
        """Gets multirequests as well, limits to just those by the current user"""
        single_req = (FOIARequest.objects.filter(user=self.request.user)
                                         .select_related('jurisdiction'))
        multi_req = FOIAMultiRequest.objects.filter(user=self.request.user)
        single_req = self.sort_list(self.filter_list(single_req))
        return list(single_req) + list(multi_req)


@class_view_decorator(login_required)
class FollowingRequestList(RequestList):
    """List of all FOIA requests the user is following"""
    def get_queryset(self):
        """Limits FOIAs to those followed by the current user"""
        objects = actstream.models.following(self.request.user, FOIARequest)
        # actstream returns a list of objects, so we have to turn it into a queryset
        pk_list = [_object.pk for _object in objects if _object]
        objects = FOIARequest.objects.filter(pk__in=pk_list)
        objects = objects.select_related('jurisdiction')
        # now we filter and sort the list like in the parent class
        objects = self.filter_list(objects)
        objects = self.sort_list(objects)
        # finally, we can only show requests visible to that user
        return objects.get_viewable(self.request.user)


class ProcessingRequestList(RequestList):
    """List all of the currently processing FOIA requests."""
    template_name = 'lists/request_processing_list.html'
    default_sort = 'date_processing'

    def dispatch(self, *args, **kwargs):
        """Only staff can see the list of processing requests."""
        if not self.request.user.is_staff:
            raise Http404()
        return super(ProcessingRequestList, self).dispatch(*args, **kwargs)

    def filter_list(self, objects):
        """Gets all processing requests"""
        objects = super(ProcessingRequestList, self).filter_list(objects)
        return objects.filter(status='submitted')

    def get_filters(self):
        """Removes the 'status' filter, because its only processing requests"""
        filters = super(ProcessingRequestList, self).get_filters()
        for filter_dict in filters:
            if 'status' in filter_dict.values():
                filters.pop(filters.index(filter_dict))
        return filters


# pylint: disable=no-self-use
class Detail(DetailView):
    """Details of a single FOIA request as well
    as handling post actions for the request"""

    model = FOIARequest
    context_object_name = 'foia'

    def dispatch(self, request, *args, **kwargs):
        """If request is a draft, then redirect to drafting interface"""
        if request.POST:
            return self.post(request)
        foia = self.get_object()
        if foia.status == 'started':
            return redirect(
                'foia-draft',
                jurisdiction=foia.jurisdiction.slug,
                jidx=foia.jurisdiction.id,
                slug=foia.slug,
                idx=foia.id
            )
        else:
            return super(Detail, self).dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        """Get the FOIA Request"""
        # pylint: disable=unused-argument
        foia = get_foia(
            self.kwargs['jurisdiction'],
            self.kwargs['jidx'],
            self.kwargs['slug'],
            self.kwargs['idx']
        )
        user = self.request.user
        valid_access_key = self.request.GET.get('key') == foia.access_key
        if not foia.viewable_by(user) and not valid_access_key:
            raise Http404()
        if foia.created_by(user):
            if foia.updated:
                foia.updated = False
                foia.save()
        return foia

    def get_context_data(self, **kwargs):
        """Add extra context data"""
        context = super(Detail, self).get_context_data(**kwargs)
        foia = context['foia']
        user = self.request.user
        user_can_edit = foia.editable_by(user)
        is_past_due = foia.date_due < datetime.now().date() if foia.date_due else False
        include_draft = user.is_staff or foia.status == 'started'
        context['all_tags'] = Tag.objects.all()
        context['past_due'] = is_past_due
        context['user_can_edit'] = user_can_edit
        context['embargo'] = {
            'show': ((user_can_edit and foia.user.profile.can_embargo)\
                    or foia.embargo) or user.is_staff,
            'edit': user_can_edit and foia.user.profile.can_embargo,
            'add': user_can_edit and user.profile.can_embargo,
            'remove': user_can_edit and foia.embargo
        }
        context['embargo_form'] = FOIAEmbargoForm(initial={
            'permanent_embargo': foia.permanent_embargo,
            'date_embargo': foia.date_embargo
        })
        context['note_form'] = FOIANoteForm()
        context['access_form'] = FOIAAccessForm()
        context['embargo_needs_date'] = foia.status in END_STATUS
        context['user_actions'] = foia.user_actions(user)
        context['noncontextual_request_actions'] = foia.noncontextual_request_actions(user)
        context['contextual_request_actions'] = foia.contextual_request_actions(user)
        context['status_choices'] = STATUS if include_draft else STATUS_NODRAFT
        context['show_estimated_date'] = foia.status not in ['submitted', 'ack', 'done', 'rejected']
        context['change_estimated_date'] = FOIAEstimatedCompletionDateForm(instance=foia)
        context['task_count'] = len(Task.objects.filter_by_foia(foia))
        context['open_tasks'] = Task.objects.get_unresolved().filter_by_foia(foia)
        context['stripe_pk'] = STRIPE_PUB_KEY
        context['sidebar_admin_url'] = reverse('admin:foia_foiarequest_change', args=(foia.pk,))
        if foia.sidebar_html:
            messages.info(self.request, foia.sidebar_html)
        return context

    def post(self, request):
        """Handle form submissions"""
        foia = self.get_object()
        actions = {
            'status': self._status,
            'tags': self._tags,
            'follow_up': self._follow_up,
            'thanks': self._thank,
            'question': self._question,
            'add_note': self._add_note,
            'flag': self._flag,
            'appeal': self._appeal,
            'date_estimate': self._update_estimate,
            'status_comm': change_comm_status,
            'move_comm': move_comm,
            'delete_comm': delete_comm,
            'resend_comm': resend_comm,
            'generate_key': self._generate_key,
            'grant_access': self._grant_access,
            'revoke_access': self._revoke_access,
            'demote': self._demote_editor,
            'promote': self._promote_viewer,
        }
        try:
            return actions[request.POST['action']](request, foia)
        except KeyError: # if submitting form from web page improperly
            return redirect(foia)

    def _tags(self, request, foia):
        """Handle updating tags"""
        # pylint: disable=no-self-use
        if foia.editable_by(request.user) or request.user.is_staff:
            foia.update_tags(request.POST.get('tags'))
        return redirect(foia)

    # pylint: disable=line-too-long
    def _status(self, request, foia):
        """Handle updating status"""
        status = request.POST.get('status')
        old_status = foia.get_status_display()
        if foia.status not in ['started', 'submitted'] and \
                ((foia.editable_by(request.user) and status in [s for s, _ in STATUS_NODRAFT]) or
                 (request.user.is_staff and status in [s for s, _ in STATUS])):
            foia.status = status
            foia.save()
            StatusChangeTask.objects.create(
                user=request.user,
                old_status=old_status,
                foia=foia,
            )
            # generate status change activity
            actstream.action.send(
                request.user,
                verb='changed the status of',
                action_object=foia
            )
        return redirect(foia)

    def _question(self, request, foia):
        """Handle asking a question"""
        text = request.POST.get('text')
        if foia.editable_by(request.user) and text:
            title = 'Question about request: %s' % foia.title
            question = Question.objects.create(
                user=request.user,
                title=title,
                slug=slugify(title),
                foia=foia,
                question=text,
                date=datetime.now()
            )
            messages.success(request, 'Your question has been posted.')
            question.notify_new()
            return redirect(question)
        return redirect(foia)

    def _add_note(self, request, foia):
        """Adds a note to the request"""
        note_form = FOIANoteForm(request.POST)
        if foia.editable_by(request.user) and note_form.is_valid():
            foia_note = note_form.save(commit=False)
            foia_note.foia = foia
            foia_note.author = request.user
            foia_note.datetime = datetime.now()
            foia_note.save()
            logging.info('%s added %s to %s', foia_note.author, foia_note, foia_note.foia)
            messages.success(request, 'Your note is attached to the request.')
            # generate note added action
            actstream.action.send(
                request.user,
                verb='added',
                action_object=foia_note,
                target=foia
            )
        return redirect(foia)

    def _flag(self, request, foia):
        """Allow a user to notify us of a problem with the request"""
        text = request.POST.get('text')
        if request.user.is_authenticated() and text:
            FlaggedTask.objects.create(
                user=request.user,
                text=text,
                foia=foia)
            messages.success(request, 'Problem succesfully reported')
            # generate flagged action
            actstream.action.send(
                request.user,
                verb='flagged',
                action_object=foia
            )
        return redirect(foia)

    def _follow_up(self, request, foia):
        """Handle submitting follow ups"""
        can_follow_up = foia.editable_by(request.user) or request.user.is_staff
        test = can_follow_up and foia.status != 'started'
        success_msg = 'Your follow up has been sent.'
        agency = foia.agency
        verb = 'followed up'
        return self._new_comm(request, foia, test, success_msg, agency, verb)

    def _thank(self, request, foia):
        """Handle submitting a thank you follow up"""
        test = foia.editable_by(request.user) and foia.is_thankable()
        success_msg = 'Your thank you has been sent.'
        agency = foia.agency
        verb = 'thanked'
        return self._new_comm(
                request, foia, test, success_msg, agency, verb, thanks=True)

    def _appeal(self, request, foia):
        """Handle submitting an appeal"""
        test = foia.editable_by(request.user) and foia.is_appealable()
        success_msg = 'Appeal successfully sent.'
        agency = foia.agency.appeal_agency if foia.agency.appeal_agency else foia.agency
        verb = 'appealed'
        return self._new_comm(
                request, foia, test, success_msg, agency, verb, appeal=True)

    def _new_comm(
            self,
            request,
            foia,
            test,
            success_msg,
            agency,
            verb,
            appeal=False,
            thanks=False,
            ):
        """Helper function for sending a new comm"""
        # pylint: disable=too-many-arguments
        text = request.POST.get('text')
        if text and test:
            save_foia_comm(
                    foia,
                    foia.user.get_full_name(),
                    text,
                    appeal=appeal,
                    thanks=thanks,
                    )
            messages.success(request, success_msg)
            # generate appeal action
            actstream.action.send(
                request.user,
                verb=verb,
                action_object=foia,
                target=agency
            )
        return redirect(foia)

    def _update_estimate(self, request, foia):
        """Change the estimated completion date"""
        form = FOIAEstimatedCompletionDateForm(request.POST, instance=foia)
        if foia.editable_by(request.user):
            if form.is_valid():
                form.save()
                messages.success(request, 'Successfully changed the estimated completion date.')
            else:
                messages.error(request, 'Invalid date provided.')
        else:
            messages.error(request, 'You cannot do that, stop it.')
        return redirect(foia)

    def _generate_key(self, request, foia):
        """Generate and return an access key, with support for AJAX."""
        if not foia.editable_by(request.user):
            if request.is_ajax():
                return PermissionDenied
            else:
                return redirect(foia)
        else:
            key = foia.generate_access_key()
            if request.is_ajax():
                return HttpResponse(json.dumps({'key': key}), 'application/json')
            else:
                messages.success(request, 'New private link created.')
                return redirect(foia)

    def _grant_access(self, request, foia):
        """Grant editor access to the specified users."""
        form = FOIAAccessForm(request.POST)
        if not foia.editable_by(request.user) or not form.is_valid():
            return redirect(foia)
        access = form.cleaned_data['access']
        users = form.cleaned_data['users']
        if access == 'edit' and users:
            for user in users:
                foia.add_editor(user)
                # generate action
                actstream.action.send(
                    request.user,
                    verb='added editor',
                    action_object=user,
                    target=foia
                )
        if access == 'view' and users:
            for user in users:
                foia.add_viewer(user)
                # generate action
                actstream.action.send(
                    request.user,
                    verb='added viewer',
                    action_object=user,
                    target=foia
                )
        if len(users) > 1:
            success_msg = '%d people can now %s this request.' % (len(users), access)
        else:
            success_msg = '%s can now %s this request.' % (users[0].first_name, access)
        messages.success(request, success_msg)
        return redirect(foia)

    def _revoke_access(self, request, foia):
        """Revoke access from a user."""
        user_pk = request.POST.get('user')
        user = User.objects.get(pk=user_pk)
        if foia.editable_by(request.user) and user:
            if foia.has_editor(user):
                foia.remove_editor(user)
            elif foia.has_viewer(user):
                foia.remove_viewer(user)
            # generate action
            actstream.action.send(
                request.user,
                verb='removed',
                action_object=user,
                target=foia
            )
            messages.success(request, '%s no longer has access to this request.' % user.first_name)
        return redirect(foia)

    def _demote_editor(self, request, foia):
        """Demote user from editor access to viewer access"""
        user_pk = request.POST.get('user')
        user = User.objects.get(pk=user_pk)
        if foia.editable_by(request.user) and user:
            foia.demote_editor(user)
            messages.success(request, '%s can now only view this request.' % user.first_name)
        return redirect(foia)

    def _promote_viewer(self, request, foia):
        """Promote user from viewer access to editor access"""
        user_pk = request.POST.get('user')
        user = User.objects.get(pk=user_pk)
        if foia.editable_by(request.user) and user:
            foia.promote_viewer(user)
            messages.success(request, '%s can now edit this request.' % user.first_name)
        return redirect(foia)

def redirect_old(request, jurisdiction, slug, idx, action):
    """Redirect old urls to new urls"""
    # pylint: disable=unused-variable
    # pylint: disable=unused-argument

    # some jurisdiction slugs changed, just ignore the jurisdiction slug passed in
    foia = get_object_or_404(FOIARequest, pk=idx)
    jurisdiction = foia.jurisdiction.slug
    jidx = foia.jurisdiction.pk

    if action == 'view':
        return redirect('/foi/%(jurisdiction)s-%(jidx)s/%(slug)s-%(idx)s/' % locals())

    if action == 'admin-fix':
        action = 'admin_fix'

    return redirect('/foi/%(jurisdiction)s-%(jidx)s/%(slug)s-%(idx)s/%(action)s/' % locals())

@user_passes_test(lambda u: u.is_staff)
def acronyms(request):
    """A page with all the acronyms explained"""
    status_dict = dict(STATUS)
    codes = [(acro, name, status_dict.get(status, ''), desc)
             for acro, (name, status, desc) in CODES.iteritems()]
    codes.sort()
    return render_to_response(
        'staff/acronyms.html',
        {'codes': codes},
        context_instance=RequestContext(request)
    )
