"""
Admin registration for Q&A models
"""

# Django
from django import forms
from django.contrib import admin
from django.contrib.auth.models import User

# Third Party
from autocomplete_light import shortcuts as autocomplete_light
from reversion.admin import VersionAdmin

# MuckRock
from muckrock.qanda.models import Answer, Question


class AnswerForm(forms.ModelForm):
    """Form with autocomplete for users"""
    user = autocomplete_light.ModelChoiceField(
        'UserAutocomplete', queryset=User.objects.all()
    )

    class Meta:
        model = Answer
        fields = '__all__'


class QuestionForm(forms.ModelForm):
    """Form with autocomplete for user and foia"""
    user = autocomplete_light.ModelChoiceField(
        'UserAutocomplete', queryset=User.objects.all()
    )
    foia = autocomplete_light.ModelChoiceField(
        'FOIARequestAdminAutocomplete', required=False
    )

    class Meta:
        model = Question
        fields = '__all__'


class AnswerInline(admin.TabularInline):
    """Answer Inline Admin"""
    model = Answer
    form = AnswerForm
    extra = 1


class QuestionAdmin(VersionAdmin):
    """Quesiton Admin"""
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'user', 'date')
    search_fields = ('title', 'question')
    inlines = [AnswerInline]
    form = QuestionForm


admin.site.register(Question, QuestionAdmin)
