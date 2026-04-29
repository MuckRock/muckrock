"""Admin configuration for the gethelp app"""

from django.contrib import admin

from muckrock.gethelp.models import Problem


class ChildProblemInline(admin.TabularInline):
    model = Problem
    fk_name = "parent"
    extra = 1
    fields = ["title", "category", "resolution", "flag_category", "order"]


class ProblemAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "parent", "order"]
    list_filter = ["category"]
    list_editable = ["order"]
    search_fields = ["title"]
    raw_id_fields = ["parent"]
    inlines = [ChildProblemInline]


admin.site.register(Problem, ProblemAdmin)
