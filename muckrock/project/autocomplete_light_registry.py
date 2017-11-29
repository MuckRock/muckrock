"""
Autocomplete registry for projects
"""

from autocomplete_light import shortcuts as autocomplete_light

from muckrock.project.models import Project

class ProjectAutocomplete(autocomplete_light.AutocompleteModelBase):
    """Creates an acutocomplete registry for projects."""
    choice_template = 'autocomplete/project.html'
    search_fields = ['title']
    attrs = {
        'date-autocomplete-minimum-characters': 2,
        'placeholder': 'Search projects'
    }

    def choices_for_request(self):
        """
        When showing possible requests to add, only show projects the user is a contributor to.
        If the user is unauthenticated, only return public choices.
        However, if the user is staff, then show them all the available projects.
        """
        self.choices = Project.objects.get_visible(self.request.user)
        return super(ProjectAutocomplete, self).choices_for_request()


class ProjectManagerAutocomplete(autocomplete_light.AutocompleteModelBase):
    """Creates an autocomplete registry for project manager components"""
    choice_template = 'autocomplete/project.html'
    search_fields = ['title', 'summary']
    attrs = {
        'data-autocomplete-minimum-characters': 0,
        'placeholder': 'Search your projects'
    }

    def choices_for_request(self):
        """
        When showing possible requests to add, only show projects the user is a contributor to.
        If the user is unauthenticated, return no projects
        However, if the user is staff, then show them all the available projects.
        """
        self.choices = Project.objects.get_manager(self.request.user)
        return super(ProjectManagerAutocomplete, self).choices_for_request()

autocomplete_light.register(Project, ProjectAutocomplete)
autocomplete_light.register(Project, ProjectManagerAutocomplete)
