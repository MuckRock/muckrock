"""
Autocomplete registry for Tags
"""

from django.db.models import Count

from autocomplete_light import shortcuts as autocomplete_light

from muckrock.tags.models import Tag


class TagAutocomplete(autocomplete_light.AutocompleteModelBase):
    """Creates an autocomplete field for picking tags"""
    choices = (Tag.objects
            .annotate(num=Count('tags_taggeditembase_items'))
            .exclude(num=0))
    search_fields = ['name']
    attrs = {
        'data-autocomplete-minimum-characters': 1,
        'placeholder': 'Search tags',
    }


class TagSlugAutocomplete(TagAutocomplete):
    """Tag autocomplete that uses the slug as the value"""

    def choice_value(self, choice):
        """Return the slug as the value"""
        return choice.slug


autocomplete_light.register(Tag, TagAutocomplete)
autocomplete_light.register(Tag, TagSlugAutocomplete)
