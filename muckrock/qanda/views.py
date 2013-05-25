"""
Views for the QandA application
"""

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.template.defaultfilters import slugify
from django.views.generic.list import ListView

from datetime import datetime

from muckrock.qanda.models import Question
from muckrock.qanda.forms import QuestionForm, AnswerForm

def question_detail(request, slug, idx):
    """Question page"""
    question = get_object_or_404(Question, slug=slug, pk=idx)
    return render_to_response('qanda/question_detail.html', {'object': question},
                              context_instance=RequestContext(request))

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


