"""
Views for the QandA application
"""

# Django
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.mail import send_mail
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic.detail import DetailView

# Third Party
import actstream

# MuckRock
from muckrock.accounts.models import Notification
from muckrock.core.views import MRSearchFilterListView
from muckrock.qanda.filters import QuestionFilterSet
from muckrock.qanda.forms import AnswerForm
from muckrock.qanda.models import Answer, Question
from muckrock.tags.models import Tag, normalize


class QuestionList(MRSearchFilterListView):
    """List of unanswered questions"""

    model = Question
    filter_class = QuestionFilterSet
    title = "Q&A Forum"
    template_name = "qanda/list.html"
    default_sort = "date"
    default_order = "desc"
    sort_map = {"title": "title", "user": "user__profile__full_name", "date": "date"}

    def get_queryset(self):
        """Hide inactive users and prefetch"""
        return (
            super(QuestionList, self)
            .get_queryset()
            .filter(user__is_active=True)
            .select_related("user")
            .prefetch_related("answers")
        )

    def get_context_data(self, **kwargs):
        """Adds an info message to the context"""
        context = super(QuestionList, self).get_context_data(**kwargs)
        info_msg = (
            "The Q&A forum is being retired.  You may browse "
            "existing questions, but asking new questions has been disabled. "
            "Have a technical support or customer service issue? Those should "
            'be reported either using the "Report" button on the request page '
            'or simply by emailing <a href="mailto:info@muckrock.com">'
            "info@muckrock.com</a>."
        )
        messages.info(self.request, info_msg)
        return context


class UnansweredQuestionList(QuestionList):
    """List of unanswered questions"""

    def get_queryset(self):
        objects = super(UnansweredQuestionList, self).get_queryset()
        return objects.annotate(num_answers=Count("answers")).filter(num_answers=0)


class Detail(DetailView):
    """Question detail view"""

    model = Question

    def get_queryset(self):
        """Select related and prefetch the query set"""
        return Question.objects.select_related(
            "foia", "foia__agency__jurisdiction__parent__parent", "foia__composer__user"
        ).filter(user__is_active=True)

    def get(self, request, *args, **kwargs):
        """Mark any unread notifications for this object as read."""
        user = request.user
        if user.is_authenticated:
            question = self.get_object()
            notifications = (
                Notification.objects.for_user(user).for_object(question).get_unread()
            )
            for notification in notifications:
                notification.mark_read()
        return super(Detail, self).get(request, *args, **kwargs)

    def post(self, request, **kwargs):
        """Edit the question or answer"""
        # pylint: disable=unused-argument

        question = self.get_object()
        obj_type = request.POST.get("object")

        if obj_type == "question":
            self._question(request, question)
        elif obj_type == "answer":
            try:
                self._answer(request)
            except Answer.DoesNotExist:
                pass

        tags = request.POST.getlist("tags")
        if tags:
            tag_set = set()
            for tag in tags:
                new_tag, _ = Tag.objects.get_or_create(name=normalize(tag))
                tag_set.add(new_tag)
            question.tags.set(tag_set)
            messages.success(request, "Your tags have been saved to this question.")

        return redirect(question)

    def _question(self, request, question):
        """Edit the question"""
        if request.user == question.user or request.user.is_staff:
            question.question = request.POST.get("question")
            question.save()
            messages.success(request, "Your question is updated.")
        else:
            messages.error(request, "You may only edit your own questions.")

    def _answer(self, request):
        """Edit an answer"""
        answer = Answer.objects.get(pk=request.POST.get("answer-pk"))
        if request.user == answer.user or request.user.is_staff:
            answer.answer = request.POST.get("answer")
            answer.save()
            messages.success(request, "Your answer is updated.")
        else:
            messages.error(request, "You may only edit your own answers.")

    def get_context_data(self, **kwargs):
        context = super(Detail, self).get_context_data(**kwargs)
        context["sidebar_admin_url"] = reverse(
            "admin:qanda_question_change", args=(context["object"].pk,)
        )
        context["answers"] = (
            context["object"]
            .answers.filter(user__is_active=True)
            .select_related("user__profile")
        )
        context["answer_form"] = AnswerForm()
        foia = self.object.foia
        if foia is not None:
            foia.public_file_count = foia.get_files().count()
        context["foia_viewable"] = foia is not None and foia.has_perm(
            self.request.user, "view"
        )
        return context


@login_required
def follow(request, slug, idx):
    """Follow or unfollow a question"""
    question = get_object_or_404(Question, slug=slug, id=idx)
    if actstream.actions.is_following(request.user, question):
        actstream.actions.unfollow(request.user, question)
        messages.success(request, "You are no longer following this question.")
    else:
        actstream.actions.follow(request.user, question, actor_only=False)
        messages.success(request, "You are now following this question.")
    return redirect(question)


@permission_required("qanda.block")
def block_user(request, model, model_pk):
    """Block the posts author from the site"""
    return _block_or_report(request, model, model_pk, block=True)


@login_required
def report_spam(request, model, model_pk):
    """Report the post as being spam"""
    return _block_or_report(request, model, model_pk, block=False)


def _block_or_report(request, model, model_pk, block):
    """Common code for blocking a user or reporting spam"""

    if model == "question":
        obj = get_object_or_404(Question.objects.select_related("user"), pk=model_pk)
        comment = obj.question
    elif model == "answer":
        obj = get_object_or_404(Answer.objects.select_related("user"), pk=model_pk)
        comment = obj.answer
    else:
        raise Http404

    if block:
        obj.user.is_active = False
        obj.user.save()
        subject = "%s blocked as spammer" % obj.user.username
    else:
        subject = "%s reported as spam" % obj.user.username

    send_mail(
        subject=subject,
        message=render_to_string(
            "text/qanda/spam.txt",
            {
                "url": obj.get_absolute_url(),
                "moderator": request.user,
                "comment": comment,
                "type": "block" if block else "report",
                "muckrock_url": settings.MUCKROCK_URL,
            },
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.DEFAULT_FROM_EMAIL],
    )

    if block:
        messages.success(request, "User succesfully blocked")
    else:
        messages.success(request, "Comment succesfully reported as spam")

    if "next" in request.GET:
        return redirect(request.GET["next"])
    else:
        return redirect("question-index")
