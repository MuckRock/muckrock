"""
Autocomplete registry for Communication
"""

from django.db.models import Q

from autocomplete_light import shortcuts as autocomplete_light

from muckrock.communication.models import (
        EmailAddress,
        PhoneNumber,
        Address,
        )


class AddressAutocomplete(autocomplete_light.AutocompleteModelTemplate):
    """An autocomplete for selecting an email address"""
    choices = Address.objects.all()
    choice_template = 'autocomplete/address.html'
    search_fields = [
            'address',
            'street',
            'city',
            'state',
            'zip_code',
            'country',
            ]
    attrs = {
        'data-autocomplete-minimum-characters': 2,
        'placeholder': 'Search for an address',
    }


class EmailAddressAutocomplete(autocomplete_light.AutocompleteModelTemplate):
    """An autocomplete for selecting an email address"""
    choices = EmailAddress.objects.all()
    search_fields = ['email', 'name']
    attrs = {
        'data-autocomplete-minimum-characters': 0,
        'placeholder': 'Search for an email address',
    }


class PhoneNumberAutocomplete(autocomplete_light.AutocompleteModelTemplate):
    """An autocomplete for selecting a phone number"""
    choices = PhoneNumber.objects.all()
    choice_template = 'autocomplete/phone.html'
    search_fields = ['number']
    attrs = {
        'data-autocomplete-minimum-characters': 0,
        'placeholder': 'Search for a phone number',
    }


class FaxAutocomplete(autocomplete_light.AutocompleteModelTemplate):
    """An autocomplete for selecting a fax number"""
    choices = PhoneNumber.objects.filter(type='fax')
    search_fields = ['number']
    attrs = {
        'data-autocomplete-minimum-characters': 0,
        'placeholder': 'Search for a fax number',
    }


class EmailOrFaxAutocomplete(autocomplete_light.AutocompleteBase):
    """An autocomplete for selecting an email or fax number"""
    attrs = {
        'data-autocomplete-minimum-characters': 0,
        'placeholder': 'Search for an email address or fax number',
    }
    def choices_for_request(self):
        query = self.request.GET.get('q', '')
        emails = list(EmailAddress.objects
                .filter(
                    Q(email__contains=query) |
                    Q(name__contains=query),
                    )[:10])
        phones = list(PhoneNumber.objects
                .filter(number__contains=query, type='fax')
                [:10])
        combined = (emails + phones)[:10]
        return [unicode(i) for i in combined]


autocomplete_light.register(Address, AddressAutocomplete,
        add_another_url_name='admin:communication_address_add')
autocomplete_light.register(EmailAddress, EmailAddressAutocomplete,
        add_another_url_name='admin:communication_emailaddress_add')
autocomplete_light.register(PhoneNumber, PhoneNumberAutocomplete,
        add_another_url_name='admin:communication_phonenumber_add')
autocomplete_light.register(PhoneNumber, FaxAutocomplete,
        add_another_url_name='admin:communication_phonenumber_add')
autocomplete_light.register(EmailOrFaxAutocomplete)
