"""
Views for the QandA application
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.template.defaultfilters import slugify
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from datetime import datetime

from muckrock.qanda.models import Question, Answer
from muckrock.qanda.forms import QuestionForm, AnswerForm

class Detail(DetailView):
    """Question detail view"""
    model = Question

    def post(self, request, **kwargs):
        """Edit the question or answer"""
        # pylint: disable=W0613

        question = self.get_object()
        obj_type = request.POST.get('object')

        if obj_type == 'question':
            self._question(request, question)
        elif obj_type == 'answer':
            try:
                self._answer(request)
            except Answer.DoesNotExist:
                pass

        return redirect(question)

    def _question(self, request, question):
        """Edit the question"""
        # pylint: disable=R0201
        if request.user == question.user or request.user.is_staff:
            question.question = request.POST.get('question')
            question.save()
            messages.success(request, 'Question succesfully updated')
        else:
            messages.error(request, 'You may only edit your own questions')

    def _answer(self, request):
        """Edit an answer"""
        # pylint: disable=R0201
        answer = Answer.objects.get(pk=request.POST.get('answer-pk'))
        if request.user == answer.user or request.user.is_staff:
            answer.answer = request.POST.get('answer')
            answer.save()
            messages.success(request, 'Answer succesfully updated')
        else:
            messages.error(request, 'You may only edit your own answers')


@login_required
def create_question(request):
    """Create a question"""

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.slug = slugify(question.title)
            question.user = request.user
            question.date = datetime.now()
            question.save()
            question.notify()
            return redirect(question)
    else:
        form = QuestionForm()

    return render_to_response('qanda/question_form.html', {'form': form},
                              context_instance=RequestContext(request))

@login_required
def create_answer(request, slug, idx):
    """Create an answer"""

    question = get_object_or_404(Question, slug=slug, pk=idx)

    if request.method == 'POST':
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.user = request.user
            answer.date = datetime.now()
            answer.question = question
            answer.save()
            return redirect(answer.question)
    else:
        form = AnswerForm()

    return render_to_response('qanda/answer_form.html', {'form': form, 'question': question},
                              context_instance=RequestContext(request))

@login_required
def subscribe(request):
    """Subscribe or unsubscribe to new questions"""
    profile = request.user.get_profile()

    if profile.follow_questions:
        profile.follow_questions = False
        messages.info(request, 'You are now unsubscribed from new question notifications')
    else:
        profile.follow_questions = True
        messages.success(request, 'You are now subscribed to new question notifications')
    profile.save()

    return redirect(reverse('question-index'))


class List(ListView):
    """List of unanswered questions"""
    paginate_by = 10
    model = Question

    def get_context_data(self, **kwargs):
        context = super(List, self).get_context_data(**kwargs)
        context['title'] = 'Questions'
        return context


class ListUnanswered(ListView):
    """List of unanswered questions"""
    paginate_by = 10
    queryset = Question.objects.annotate(num_answers=Count('answers')).filter(num_answers=0)

    def get_context_data(self, **kwargs):
        context = super(ListUnanswered, self).get_context_data(**kwargs)
        context['title'] = 'Unanswered Questions'
        return context


class ListRecent(ListView):
    """List of recently answered questions"""
    paginate_by = 10
    queryset = Question.objects.exclude(answer_date=None).order_by('-answer_date')

    def get_context_data(self, **kwargs):
        context = super(ListRecent, self).get_context_data(**kwargs)
        context['title'] = 'Recently Answered Questions'
        return context


