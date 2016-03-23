"""
Admin registration for Q&A models
"""

from django.contrib import admin

from reversion.admin import VersionAdmin

from muckrock.qanda.models import Question, Answer

# These inhereit more than the allowed number of public methods
# pylint: disable=too-many-public-methods

class AnswerInline(admin.TabularInline):
    """Answer Inline Admin"""
    model = Answer
    extra = 1

class QuestionAdmin(VersionAdmin):
    """Quesiton Admin"""
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'user', 'date')
    search_fields = ('title', 'question')
    inlines = [AnswerInline]

admin.site.register(Question, QuestionAdmin)
