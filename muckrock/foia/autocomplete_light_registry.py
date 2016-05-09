"""
Autocomplete registry for FOIA Requests
"""

from muckrock.foia.models import FOIARequest

from autocomplete_light import shortcuts as autocomplete_light

class FOIARequestAutocomplete(autocomplete_light.AutocompleteModelTemplate):
    """Creates an autocomplete field for picking FOIA requests"""
    choices = FOIARequest.objects.all().select_related('agency__jurisdiction')
    choice_template = 'autocomplete/foia.html'
    search_fields = ['title', 'pk']
    attrs = {
        'placeholder': 'Search for requests',
        'data-autocomplete-minimum-characters': 1
    }
    def choices_for_request(self):
        query = self.request.GET.get('q', '')
        conditions = self._choices_for_request_conditions(query, self.search_fields)
        choices = self.choices.get_viewable(self.request.user).filter(conditions)
        return self.order_choices(choices)[0:self.limit_choices]

autocomplete_light.register(FOIARequest, FOIARequestAutocomplete)

autocomplete_light.register(
    FOIARequest,
    name='FOIARequestAdminAutocomplete',
    choices=FOIARequest.objects.all(),
    search_fields=('title',),
    attrs={
        'placeholder': 'Search for requests',
        'data-autocomplete-minimum-characters': 1})
