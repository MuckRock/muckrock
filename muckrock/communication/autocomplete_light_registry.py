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
            'suite',
            'city',
            'state',
            'zip_code',
            ]
    attrs = {
        'data-autocomplete-minimum-characters': 2,
        'placeholder': 'Search for an address',
    }


class EmailAddressAutocomplete(autocomplete_light.AutocompleteModelTemplate):
    """An autocomplete for selecting an email address"""
    choices = EmailAddress.objects.filter(status='good')
    search_fields = ['email', 'name']
    attrs = {
        'data-autocomplete-minimum-characters': 0,
        'placeholder': 'Search for an email address',
    }


class EmailAddressAdminAutocomplete(EmailAddressAutocomplete):
    """Allow choosing error emails in the admin"""
    choices = EmailAddress.objects.all()


class GenericPhoneNumberAutocomplete(autocomplete_light.AutocompleteModelTemplate):
    """Logic for querying numbers"""
    def choices_for_request(self):
        """Remove parentheses and convert spaces to dashes before searching"""
        query = self.request.GET.get('q', '')
        query = query.translate({
            ord(u'('): None,
            ord(u')'): None,
            ord(u' '): u'-',
            })
        choices = self.choices.filter(
                number__contains=query,
                )
        return self.order_choices(choices)[0:self.limit_choices]


class PhoneNumberAutocomplete(GenericPhoneNumberAutocomplete):
    """An autocomplete for selecting a phone number"""
    choices = PhoneNumber.objects.all()
    choice_template = 'autocomplete/phone.html'
    search_fields = ['number']
    attrs = {
        'data-autocomplete-minimum-characters': 0,
        'placeholder': 'Search for a phone number',
    }


class FaxAutocomplete(GenericPhoneNumberAutocomplete):
    """An autocomplete for selecting a fax number"""
    choices = PhoneNumber.objects.filter(status='good', type='fax')
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
                .filter(status='good')
                .filter(
                    Q(email__icontains=query) |
                    Q(name__icontains=query),
                    )[:10])
        phones = list(PhoneNumber.objects
                .filter(status='good')
                .filter(number__contains=query, type='fax')
                [:10])
        combined = (emails + phones)[:10]
        return [unicode(i) for i in combined]


autocomplete_light.register(Address, AddressAutocomplete,
        name='AddressAdminAutocomplete',
        add_another_url_name='admin:communication_address_add')

autocomplete_light.register(EmailAddress, EmailAddressAutocomplete)
autocomplete_light.register(EmailAddress, EmailAddressAdminAutocomplete,
        add_another_url_name='admin:communication_emailaddress_add')

autocomplete_light.register(PhoneNumber, PhoneNumberAutocomplete)
autocomplete_light.register(PhoneNumber, PhoneNumberAutocomplete,
        name='PhoneNumberAdminAutocomplete',
        add_another_url_name='admin:communication_phonenumber_add')
autocomplete_light.register(PhoneNumber, FaxAutocomplete,
        name='FaxAutocomplete',
        )
autocomplete_light.register(PhoneNumber, FaxAutocomplete,
        name='FaxAdminAutocomplete',
        add_another_url_name='admin:communication_phonenumber_add')

autocomplete_light.register(EmailOrFaxAutocomplete)
