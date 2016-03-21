"""
Autocomplete registry for projects
"""

from autocomplete_light import shortcuts as autocomplete_light

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
        user = self.request.user
        if not user.is_staff:
            self.choices = self.choices.filter(contributors=user)
        choices = super(ProjectManagerAutocomplete, self).choices_for_request()
        return choices

autocomplete_light.register(Project, ProjectManagerAutocomplete)
