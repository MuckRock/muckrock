"""
Forms for Task app
"""

# Django
from django import forms

# Standard Library
import logging

# Third Party
from dal import forward
from dal_select2.widgets import ListSelect2

# MuckRock
from muckrock.accounts.models import Notification
from muckrock.agency.models import Agency
from muckrock.communication.utils import get_email_or_fax
from muckrock.core import autocomplete
from muckrock.core.utils import generate_status_action
from muckrock.foia.codes import CODE_CHOICES, CODES
from muckrock.foia.models import STATUS
from muckrock.jurisdiction.models import Jurisdiction


class FlaggedTaskForm(forms.Form):
    """Simple form for acting on a FlaggedTask"""

    text = forms.CharField(
        widget=forms.Textarea(attrs={"placeholder": "Write your reply here"})
    )


class ProjectReviewTaskForm(forms.Form):
    """Simple form for acting on a FlaggedTask"""

    reply = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"placeholder": "Write your reply here"}),
    )


class ReviewAgencyTaskForm(forms.Form):
    """Simple form to allow selecting an email address or fax number"""

    email_or_fax = forms.CharField(
        label="Update email or fax on checked requests:",
        required=False,
        widget=ListSelect2(
            url="email-fax-autocomplete",
            attrs={"data-placeholder": "Search for an email address or fax number"},
        ),
    )
    update_agency_info = forms.BooleanField(
        label="Update agency's main contact info?", required=False
    )
    snail_mail = forms.BooleanField(
        label="Make snail mail the prefered communication method", required=False
    )
    resolve = forms.BooleanField(label="Resolve after updating", required=False)
    reply = forms.CharField(
        label="Reply:", required=False, widget=forms.Textarea(attrs={"rows": 5})
    )

    def clean_email_or_fax(self):
        """Validate the email_or_fax field"""
        if self.cleaned_data["email_or_fax"]:
            return get_email_or_fax(self.cleaned_data["email_or_fax"])
        else:
            return None

    def clean(self):
        """Make email_or_fax required if snail mail is not checked"""
        cleaned_data = super().clean()
        email_or_fax = cleaned_data.get("email_or_fax")
        snail_mail = cleaned_data.get("snail_mail")

        if not email_or_fax and not snail_mail:
            self.add_error("email_or_fax", "Required if snail mail is not checked")


class ResponseTaskForm(forms.Form):
    """Simple form for acting on a ResponseTask"""

    move = forms.CharField(required=False)
    tracking_number = forms.CharField(required=False)
    price = forms.DecimalField(required=False)
    date_estimate = forms.DateField(
        label="Estimated completion date",
        required=False,
        widget=forms.DateInput(format="%m/%d/%Y", attrs={"placeholder": "mm/dd/yyyy"}),
        input_formats=[
            "%Y-%m-%d",  # '2006-10-25'
            "%m/%d/%Y",  # '10/25/2006'
            "%m/%d/%y",  # '10/25/06'
            "%b %d %Y",  # 'Oct 25 2006'
            "%b %d, %Y",  # 'Oct 25, 2006'
            "%d %b %Y",  # '25 Oct 2006'
            "%d %b, %Y",  # '25 Oct, 2006'
            "%B %d %Y",  # 'October 25 2006'
            "%B %d, %Y",  # 'October 25, 2006'
            "%d %B %Y",  # '25 October 2006'
            "%d %B, %Y",
        ],  # '25 October, 2006'
    )
    status = forms.ChoiceField(choices=STATUS)
    code = forms.ChoiceField(choices=CODE_CHOICES)
    set_foia = forms.BooleanField(
        label="Set request status", initial=True, required=False
    )
    proxy = forms.BooleanField(required=False, widget=forms.HiddenInput())

    # allows disabling of scan checking in subclasses
    check_scans = True

    def __init__(self, *args, **kwargs):
        if self.check_scans:
            task = kwargs.pop("task")
        super().__init__(*args, **kwargs)
        if self.check_scans and task.scan:
            del self.fields["status"]
        else:
            del self.fields["code"]

    def clean_move(self):
        """Splits a comma separated string into an array"""
        move_string = self.cleaned_data["move"]
        if not move_string:
            return []
        move_list = move_string.split(",")
        for string in move_list:
            string = string.strip()
        return move_list

    def process_form(self, task, user):
        """Handle the form for the task"""
        cleaned_data = self.cleaned_data
        # move is executed first, so that the status and tracking
        # operations are applied to the correct FOIA request
        comms = [task.communication]
        error_msgs = []
        action_taken = False

        steps = [
            (
                cleaned_data.get("status"),
                lambda s: self.set_status(s, cleaned_data["set_foia"], comms),
                "You tried to set the request to an invalid status.",
            ),
            (
                cleaned_data.get("code"),
                lambda c: self.set_code(c, cleaned_data["set_foia"], comms),
                "You tried to set the request to an invalid code.",
            ),
            (
                cleaned_data["tracking_number"],
                lambda t: self.set_tracking_id(t, comms),
                "You tried to set an invalid tracking id. "
                "Just use a string of characters.",
            ),
            (
                cleaned_data["date_estimate"],
                lambda d: self.set_date_estimate(d, comms),
                "You tried to set the request to an invalid date.",
            ),
            (
                cleaned_data["price"],
                lambda p: self.set_price(p, comms),
                "You tried to set a non-numeric price.",
            ),
        ]

        if cleaned_data["move"]:
            action_taken = True
            try:
                comms = self.move_communication(
                    task.communication, cleaned_data["move"], user
                )
            except ValueError:
                error_msgs.append("No valid destination for moving the request.")

        for value, func, error_msg in steps:
            if value:
                action_taken = True
                try:
                    func(value)
                except ValueError:
                    error_msgs.append(error_msg)

        if cleaned_data["proxy"]:
            action_taken = True
            self.proxy_reject(comms)

        return (action_taken, error_msgs)

    def move_communication(self, communication, foia_pks, user):
        """Moves the associated communication to a new request"""
        return communication.move(foia_pks, user)

    def set_tracking_id(self, tracking_id, comms):
        """Sets the tracking ID of the communication's request"""
        if not isinstance(tracking_id, str):
            raise ValueError("Tracking ID should be a unicode string.")
        for comm in comms:
            if not comm.foia:
                raise ValueError("The task communication is an orphan.")
            foia = comm.foia
            foia.add_tracking_id(tracking_id)
            foia.save(comment="response task tracking id")

    def set_status(self, status, set_foia, comms, title=None, body=None):
        """Sets status of comm and foia"""
        # check that status is valid
        if status is not None and status not in [
            status_set[0] for status_set in STATUS
        ]:
            raise ValueError("Invalid status.")
        for comm in comms:
            # save comm first
            if status is not None:
                comm.status = status
            if body is not None:
                comm.communication = body
            if title is not None and comm.files.count() == 1:
                comm.files.update(title=title)
            comm.save()
            # save foia next, unless just updating comm status
            if set_foia:
                foia = comm.foia
                if status is not None:
                    foia.status = status
                if status in ["rejected", "no_docs", "done", "abandoned"]:
                    foia.datetime_done = comm.datetime
                foia.update()
                foia.save(comment="response task status")
                logging.info('Request #%d status changed to "%s"', foia.id, status)
                action = generate_status_action(foia)
                foia.notify(action)
                # Mark generic '<Agency> sent a communication to <FOIARequest> as read.'
                # https://github.com/MuckRock/muckrock/issues/1003
                generic_notifications = (
                    Notification.objects.for_object(foia)
                    .get_unread()
                    .filter(action__verb="sent a communication")
                )
                for generic_notification in generic_notifications:
                    generic_notification.mark_read()

    def set_code(self, code, set_foia, comms):
        """Sets status of comm and foia based on scan code"""
        # check that code is valid
        if code not in CODES:
            raise ValueError("Invalid code.")
        title, status, body = CODES[code]
        self.set_status(status, set_foia, comms, title=title, body=body)

        if code == "REJ-P":
            for comm in comms:
                comm.foia.proxy_reject()

    def set_price(self, price, comms):
        """Sets the price of the communication's request"""
        price = float(price)
        for comm in comms:
            if not comm.foia:
                raise ValueError("This tasks's communication is an orphan.")
            foia = comm.foia
            foia.price = price
            foia.save(comment="response task price")

    def set_date_estimate(self, date_estimate, comms):
        """Sets the estimated completion date of the communication's request."""
        for comm in comms:
            foia = comm.foia
            foia.date_estimate = date_estimate
            foia.update()
            foia.save(comment="response task date estimate")
            logging.info("Estimated completion date set to %s", date_estimate)

    def proxy_reject(self, comms):
        """Special handling for a proxy reject"""
        for comm in comms:
            comm.status = "rejected"
            comm.save()
            foia = comm.foia
            foia.status = "rejected"
            foia.proxy_reject()
            foia.update()
            foia.save(comment="response task proxy reject")
            action = generate_status_action(foia)
            foia.notify(action)


class IncomingPortalForm(ResponseTaskForm):
    """Form for incoming portal tasks, based on the response task form"""

    keep_hidden = forms.BooleanField(required=False)
    word_to_pass = forms.CharField(label="Password", max_length=20, required=False)
    communication = forms.CharField(widget=forms.Textarea(), required=False)

    # skip checking the task for if it is a scan (only applicable to response tasks)
    check_scans = False


class ReplaceNewAgencyForm(forms.Form):
    """Form for rejecting and replacing a new agency"""

    replace_jurisdiction = forms.ModelChoiceField(
        queryset=Jurisdiction.objects.filter(hidden=False),
        widget=autocomplete.ModelSelect2(
            url="jurisdiction-autocomplete",
            attrs={"data-placeholder": "Search for jurisdiction"},
        ),
    )
    replace_agency = forms.ModelChoiceField(
        label="Move this agency's requests to:",
        queryset=Agency.objects.filter(status="approved"),
        widget=autocomplete.ModelSelect2(
            url="agency-autocomplete",
            forward=(forward.Field("replace_jurisdiction", "jurisdiction"),),
            attrs={"data-placeholder": "Search agencies"},
        ),
    )


class BulkNewAgencyTaskForm(forms.Form):
    """Form for creating blank new agencies"""

    name = forms.CharField(max_length=255)
    jurisdiction = forms.ModelChoiceField(
        queryset=Jurisdiction.objects.filter(hidden=False),
        widget=autocomplete.ModelSelect2(
            url="jurisdiction-autocomplete",
            attrs={"data-placeholder": "Search for jurisdiction", "data-width": "30%"},
        ),
    )


BulkNewAgencyTaskFormSet = forms.formset_factory(BulkNewAgencyTaskForm, extra=10)
