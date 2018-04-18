"""
Forms for Task app
"""

# Django
from django import forms

# Standard Library
import logging

# Third Party
from autocomplete_light import shortcuts as autocomplete_light

# MuckRock
from muckrock.accounts.models import Notification
from muckrock.agency.models import Agency
from muckrock.communication.utils import get_email_or_fax
from muckrock.foia.models import STATUS
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.utils import generate_status_action


class FlaggedTaskForm(forms.Form):
    """Simple form for acting on a FlaggedTask"""
    text = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'Write your reply here'
        })
    )


class ProjectReviewTaskForm(forms.Form):
    """Simple form for acting on a FlaggedTask"""
    reply = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Write your reply here'
        })
    )


class StaleAgencyTaskForm(forms.Form):
    """Simple form for acting on a StaleAgencyTask"""
    email = forms.EmailField()


class ReviewAgencyTaskForm(forms.Form):
    """Simple form to allow selecting an email address or fax number"""
    email_or_fax = forms.CharField(
        label='Update email or fax on checked requests:',
        widget=autocomplete_light.TextWidget('EmailOrFaxAutocomplete'),
        required=False,
    )
    update_agency_info = forms.BooleanField(
        label='Update agency\'s main contact info?',
        required=False,
    )
    snail_mail = forms.BooleanField(
        label='Make snail mail the prefered communication method',
        required=False,
    )
    resolve = forms.BooleanField(
        label='Resolve after updating',
        required=False,
    )
    reply = forms.CharField(
        label='Reply:',
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 5,
        }),
    )

    def clean_email_or_fax(self):
        """Validate the email_or_fax field"""
        if self.cleaned_data['email_or_fax']:
            return get_email_or_fax(self.cleaned_data['email_or_fax'])
        else:
            return None

    def clean(self):
        """Make email_or_fax required if snail mail is not checked"""
        cleaned_data = super(ReviewAgencyTaskForm, self).clean()
        email_or_fax = cleaned_data.get('email_or_fax')
        snail_mail = cleaned_data.get('snail_mail')

        if not email_or_fax and not snail_mail:
            self.add_error(
                'email_or_fax',
                'Required if snail mail is not checked',
            )


class ResponseTaskForm(forms.Form):
    """Simple form for acting on a ResponseTask"""
    move = forms.CharField(required=False)
    tracking_number = forms.CharField(required=False)
    price = forms.DecimalField(required=False)
    date_estimate = forms.DateField(
        label='Estimated completion date',
        required=False,
        widget=forms.DateInput(
            format='%m/%d/%Y', attrs={
                'placeholder': 'mm/dd/yyyy'
            }
        ),
        input_formats=[
            '%Y-%m-%d',  # '2006-10-25'
            '%m/%d/%Y',  # '10/25/2006'
            '%m/%d/%y',  # '10/25/06'
            '%b %d %Y',  # 'Oct 25 2006'
            '%b %d, %Y',  # 'Oct 25, 2006'
            '%d %b %Y',  # '25 Oct 2006'
            '%d %b, %Y',  # '25 Oct, 2006'
            '%B %d %Y',  # 'October 25 2006'
            '%B %d, %Y',  # 'October 25, 2006'
            '%d %B %Y',  # '25 October 2006'
            '%d %B, %Y'
        ]  # '25 October, 2006'
    )
    status = forms.ChoiceField(choices=STATUS)
    set_foia = forms.BooleanField(
        label='Set request status', initial=True, required=False
    )
    proxy = forms.BooleanField(required=False, widget=forms.HiddenInput())

    def clean_move(self):
        """Splits a comma separated string into an array"""
        move_string = self.cleaned_data['move']
        if not move_string:
            return []
        move_list = move_string.split(',')
        for string in move_list:
            string = string.strip()
        return move_list

    def process_form(self, task, user):
        """Handle the form for the task"""
        cleaned_data = self.cleaned_data
        status = cleaned_data['status']
        set_foia = cleaned_data['set_foia']
        move = cleaned_data['move']
        tracking_number = cleaned_data['tracking_number']
        date_estimate = cleaned_data['date_estimate']
        price = cleaned_data['price']
        proxy = cleaned_data['proxy']
        # move is executed first, so that the status and tracking
        # operations are applied to the correct FOIA request
        comms = [task.communication]
        error_msgs = []
        if move:
            try:
                comms = self.move_communication(task.communication, move, user)
            except ValueError:
                error_msgs.append(
                    'No valid destination for moving the request.'
                )
        if status:
            try:
                self.set_status(status, set_foia, comms)
            except ValueError:
                error_msgs.append(
                    'You tried to set the request to an invalid status.'
                )
        if tracking_number:
            try:
                self.set_tracking_id(tracking_number, comms)
            except ValueError:
                error_msgs.append(
                    'You tried to set an invalid tracking id. Just use a string of characters.'
                )
        if date_estimate:
            try:
                self.set_date_estimate(date_estimate, comms)
            except ValueError:
                error_msgs.append(
                    'You tried to set the request to an invalid date.'
                )
        if price:
            try:
                self.set_price(price, comms)
            except ValueError:
                error_msgs.append('You tried to set a non-numeric price.')
        if proxy:
            self.proxy_reject(comms)
        action_taken = move or status or tracking_number or price or proxy
        return (action_taken, error_msgs)

    def move_communication(self, communication, foia_pks, user):
        """Moves the associated communication to a new request"""
        return communication.move(foia_pks, user)

    def set_tracking_id(self, tracking_id, comms):
        """Sets the tracking ID of the communication's request"""
        if not isinstance(tracking_id, unicode):
            raise ValueError('Tracking ID should be a unicode string.')
        for comm in comms:
            if not comm.foia:
                raise ValueError('The task communication is an orphan.')
            foia = comm.foia
            foia.add_tracking_id(tracking_id)
            foia.save(comment='response task tracking id')

    def set_status(self, status, set_foia, comms):
        """Sets status of comm and foia"""
        # check that status is valid
        if status not in [status_set[0] for status_set in STATUS]:
            raise ValueError('Invalid status.')
        for comm in comms:
            # save comm first
            comm.status = status
            comm.save()
            # save foia next, unless just updating comm status
            if set_foia:
                foia = comm.foia
                foia.status = status
                if status in ['rejected', 'no_docs', 'done', 'abandoned']:
                    foia.datetime_done = comm.date
                foia.update()
                foia.save(comment='response task status')
                logging.info(
                    'Request #%d status changed to "%s"', foia.id, status
                )
                action = generate_status_action(foia)
                foia.notify(action)
                # Mark generic '<Agency> sent a communication to <FOIARequest> as read.'
                # https://github.com/MuckRock/muckrock/issues/1003
                generic_notifications = (
                    Notification.objects.for_object(foia)
                    .get_unread().filter(action__verb='sent a communication')
                )
                for generic_notification in generic_notifications:
                    generic_notification.mark_read()

    def set_price(self, price, comms):
        """Sets the price of the communication's request"""
        price = float(price)
        for comm in comms:
            if not comm.foia:
                raise ValueError('This tasks\'s communication is an orphan.')
            foia = comm.foia
            foia.price = price
            foia.save(comment='response task price')

    def set_date_estimate(self, date_estimate, comms):
        """Sets the estimated completion date of the communication's request."""
        for comm in comms:
            foia = comm.foia
            foia.date_estimate = date_estimate
            foia.update()
            foia.save(comment='response task date estimate')
            logging.info('Estimated completion date set to %s', date_estimate)

    def proxy_reject(self, comms):
        """Special handling for a proxy reject"""
        for comm in comms:
            comm.status = 'rejected'
            comm.save()
            foia = comm.foia
            foia.status = 'rejected'
            foia.proxy_reject()
            foia.update()
            foia.save(comment='response task proxy reject')
            action = generate_status_action(foia)
            foia.notify(action)


class IncomingPortalForm(ResponseTaskForm):
    """Form for incoming portal tasks, based on the response task form"""
    keep_hidden = forms.BooleanField(required=False)
    word_to_pass = forms.CharField(
        label='Password',
        max_length=20,
        required=False,
    )
    communication = forms.CharField(widget=forms.Textarea(), required=False)


class ReplaceNewAgencyForm(forms.Form):
    """Form for rejecting and replacing a new agency"""
    replace_jurisdiction = autocomplete_light.ModelChoiceField(
        'JurisdictionAutocomplete',
        queryset=Jurisdiction.objects.all(),
    )
    replace_agency = autocomplete_light.ModelChoiceField(
        'AgencyAutocomplete',
        label='Move this agency\'s requests to:',
        queryset=Agency.objects.filter(status='approved'),
    )


class BulkNewAgencyTaskForm(forms.Form):
    """Form for creating blank new agencies"""
    name = forms.CharField(max_length=255)
    jurisdiction = forms.ModelChoiceField(
        widget=autocomplete_light.ChoiceWidget('JurisdictionAutocomplete'),
        queryset=Jurisdiction.objects.all(),
    )


BulkNewAgencyTaskFormSet = forms.formset_factory(
    BulkNewAgencyTaskForm,
    extra=10,
)
