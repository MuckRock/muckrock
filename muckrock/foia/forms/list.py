"""
FOIA forms used on list pages
"""

# Django
from django import forms

# Standard Library
import json

# MuckRock
from muckrock.foia.models import FOIASavedSearch, SearchJurisdiction


class SaveSearchForm(forms.Form):
    """A form to save search/filter params in a list view"""
    search_title = forms.CharField(
        label='Save Search',
        required=False,
    )


class SaveSearchFormHandler(object):
    """Help process the combined data from the save search form and the
    filter form
    """

    def __init__(self, request, filter_class):
        self.data = request.POST
        self.request = request
        self.filter_form = filter_class(self.data, request=request).form
        self.save_form = SaveSearchForm(self.data)

    def is_valid(self):
        """Is the data valid?"""
        return (
            self.filter_form.is_valid() and self.save_form.is_valid()
            and self.save_form.cleaned_data['search_title']
        )

    def get_clean_data(self):
        """Get the cleaned data from the form"""
        cleaned_data = self.filter_form.cleaned_data
        cleaned_data.update(self.save_form.cleaned_data)
        cleaned_data['date_range'] = self.clean_date_range(
            cleaned_data.get('date_range')
        )
        cleaned_data['jurisdiction'] = self.clean_jurisdiction(
            cleaned_data.get('jurisdiction')
        )
        return cleaned_data

    def clean_date_range(self, date_range):
        """Process the date range"""
        if date_range is None:
            return (None, None)
        date_start = date_range.start.date() if date_range.start else None
        date_stop = date_range.stop.date() if date_range.stop else None
        return (date_start, date_stop)

    def clean_jurisdiction(self, jurisdictions):
        """Convert a python repr of a list of strings into a list of strings
        into a list of tuples (jurisdiction.pk, bool indicating if we should
        include localities)"""
        # remove leading u and convert quotes so we can use json decode
        if not jurisdictions:
            return []
        jurisdictions = jurisdictions.replace("u'", "'").replace("'", '"')
        jurisdictions = json.loads(jurisdictions)
        jurisdictions = [j.split('-') for j in jurisdictions]
        return [(jid, include_local == 'True')
                for jid, include_local in jurisdictions]

    def create_saved_search(self):
        """Create a saved search"""
        cleaned_data = self.get_clean_data()
        saved_search, _ = FOIASavedSearch.objects.update_or_create(
            user=self.request.user,
            title=cleaned_data['search_title'],
            defaults={
                'query': self.data.get('q', ''),
                'status': cleaned_data.get('status', ''),
                'embargo': cleaned_data.get('has_embargo'),
                'exclude_crowdfund': cleaned_data.get('has_crowdfund'),
                'min_pages': cleaned_data.get('minimum_pages'),
                'min_date': cleaned_data['date_range'][0],
                'max_date': cleaned_data['date_range'][1],
            }
        )
        saved_search.users.set(cleaned_data.get('user', []))
        saved_search.agencies.set(cleaned_data.get('agency', []))
        saved_search.projects.set(cleaned_data.get('projects', []))
        saved_search.tags.set(cleaned_data.get('tags', []))

        saved_search.searchjurisdiction_set.all().delete()
        for jid, include_local in cleaned_data.get('jurisdiction', []):
            SearchJurisdiction.objects.create(
                search=saved_search,
                jurisdiction_id=jid,
                include_local=include_local,
            )

        return saved_search
