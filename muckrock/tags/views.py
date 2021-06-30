"""
Views for tags
"""

# Django
from django.db.models import Count
from django.views.generic import DetailView, TemplateView

# MuckRock
from muckrock.core.views import MRAutocompleteView
from muckrock.foia.models import FOIARequest
from muckrock.news.models import Article
from muckrock.project.models import Project
from muckrock.qanda.models import Question
from muckrock.tags.forms import TagForm
from muckrock.tags.models import Tag


def list_all_tags():
    """Should list all tags that exist and that have at least one object"""
    return (
        Tag.objects.annotate(num_times=Count("tags_taggeditembase_items"))
        .exclude(num_times=0)
        .order_by("name")
    )


class TagListView(TemplateView):
    """Presents a list of all tags"""

    template_name = "tags/tag_list.html"

    def get_context_data(self, **kwargs):
        """Adds all tags to context data"""
        context = super(TagListView, self).get_context_data(**kwargs)
        context["tags_length"] = list_all_tags().count()
        context["popular_tags"] = list_all_tags().order_by("-num_times")[:10]
        context["form"] = TagForm()
        return context


class TagDetailView(DetailView):
    """Presents the details of a tag"""

    model = Tag
    template_name = "tags/tag_list.html"
    max_per_type = 5

    def _get_and_count(self, context, name, queryset):
        """Get the max items per type and a total count for the queyseta
        and store into the context dictionary"""
        context[name] = queryset[: self.max_per_type]
        context[name + "_count"] = queryset.count()

    def get_context_data(self, **kwargs):
        """Adds all tags to context data"""
        context = super(TagDetailView, self).get_context_data(**kwargs)
        context["tags_length"] = list_all_tags().count()
        context["form"] = TagForm()
        user = self.request.user
        this_tag = self.get_object()

        self._get_and_count(
            context,
            "tagged_projects",
            Project.objects.get_viewable(user).filter(tags=this_tag).optimize(),
        )
        self._get_and_count(
            context,
            "tagged_requests",
            FOIARequest.objects.get_viewable(self.request.user)
            .filter(tags=this_tag)
            .select_related_view(),
        )
        self._get_and_count(
            context,
            "tagged_articles",
            Article.objects.get_published()
            .filter(tags=this_tag)
            .prefetch_related("authors", "authors__profile", "projects"),
        )
        self._get_and_count(
            context,
            "tagged_questions",
            Question.objects.filter(tags__name__in=[this_tag]),
        )
        return context


class TagAutocomplete(MRAutocompleteView):
    """Autocomplete for jurisdictions"""

    queryset = Tag.objects.annotate(num=Count("tags_taggeditembase_items")).exclude(
        num=0
    )
    search_fields = ["name"]

    def get_result_value(self, result):
        """Optionally use the slug as the value"""
        if "slug" in self.forwarded:
            return result.slug
        else:
            return result.pk
