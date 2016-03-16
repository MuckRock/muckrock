"""
Autocomplete registry for projects
"""

import autocomplete_light

from muckrock.project.models import Project

class ProjectManagerAutocomplete(autocomplete_light.AutocompleteModelBase):
    """Creates an autocomplete registry for project manager components"""
    search_fields = ['title', 'summary']
    attrs = {
        'data-autocomplete-minimum-characters': 0
    }

    def choices_for_request(self):
        """
        When showing possible requests to add, only show projects the user is a contributor to.
        However, if the user is staff, then show them all the available projects.
        """
        query = self.request.GET.get('q', '')
        user = self.request.user
        choices = super(ProjectManagerAutocomplete, self).choices_for_request()
        if not user.is_staff:
            choices = choices.filter(contributors=user)
        return choices

autocomplete_light.register(Project, ProjectManagerAutocomplete)
