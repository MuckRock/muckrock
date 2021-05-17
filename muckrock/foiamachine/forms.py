"""
Forms for FOIA Machine
"""

# Django
from django import forms

# Third Party
import bleach

# MuckRock
from muckrock.core import autocomplete
from muckrock.foiamachine.models import (
    STATUS,
    FoiaMachineCommunication,
    FoiaMachineRequest,
)

MAX_UPLOAD_SIZE = 10485760  # 10mB
ALLOWED_CONTENT_TYPES = ["application", "image", "video", "text"]


class FoiaMachineBulkRequestForm(forms.Form):
    """This allows a basic mechanism for bulk-updating requests."""

    status = forms.ChoiceField(choices=STATUS, required=False)


class FoiaMachineRequestForm(forms.ModelForm):
    """The FOIA Machine Request form provides a basis for creating and
    updating requests."""

    class Meta:
        model = FoiaMachineRequest
        fields = ["title", "status", "request_language", "jurisdiction", "agency"]
        widgets = {
            "agency": autocomplete.ModelSelect2(
                url="agency-autocomplete",
                attrs={"data-placeholder": "Search agencies"},
                forward=("jurisdiction",),
            ),
            "jurisdiction": autocomplete.ModelSelect2(
                url="jurisdiction-autocomplete",
                attrs={"data-placeholder": "Search jurisdictions"},
            ),
        }
        labels = {"request_language": "Request"}

    def clean(self):
        """Ensures the agency belongs to the jurisdiction."""
        cleaned_data = super(FoiaMachineRequestForm, self).clean()
        jurisdiction = cleaned_data.get("jurisdiction")
        agency = cleaned_data.get("agency")
        if agency and agency.jurisdiction != jurisdiction:
            raise forms.ValidationError(
                "This agency does not belong to the jurisdiction."
            )
        return cleaned_data


class FoiaMachineCommunicationForm(forms.ModelForm):
    """
    The FOIA Machine Communication form allows for creating and updating communications.
    Also allows files to be attached to the request.
    """

    def __init__(self, *args, **kwargs):
        super(FoiaMachineCommunicationForm, self).__init__(*args, **kwargs)
        if "message" in list(self.initial.keys()):
            self.initial["message"] = self.initial["message"].replace("<div>", "")
            self.initial["message"] = self.initial["message"].replace("</div>", "\n")
            self.initial["message"] = self.initial["message"].replace("<br>", "\n")
            self.initial["message"] = bleach.clean(self.initial["message"], strip=True)

    files = forms.FileField(
        required=False,
        help_text="The maximum upload size is 10MB.",
        widget=forms.ClearableFileInput(attrs={"multiple": True}),
    )
    status = forms.ChoiceField(
        choices=STATUS, required=False, label="Update request status"
    )

    def clean_files(self):
        """Enforces a size and filetype limit on uploaded files."""
        # pylint: disable=protected-access
        if not self.files:
            return []
        files = self.files.getlist("files")
        for file_ in files:
            content_type = file_.content_type.split("/")[0]
            if content_type in ALLOWED_CONTENT_TYPES:
                if file_.size > MAX_UPLOAD_SIZE:
                    raise forms.ValidationError("This file is too large.")
            else:
                raise forms.ValidationError("Unsupported filetype.")
        return files

    class Meta:
        model = FoiaMachineCommunication
        fields = [
            "request",
            "date",
            "sender",
            "receiver",
            "subject",
            "message",
            "received",
        ]
        widgets = {"request": forms.HiddenInput()}
        help_texts = {
            "sender": "What is the name or email of who sent the message?",
            "receiver": "What is the name or email of who the message was sent to?",
            "received": "Was this message sent to you?",
        }
