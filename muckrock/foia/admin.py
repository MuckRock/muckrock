"""
Admin registration for FOIA models
"""

# Django
from django import forms
from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, Max
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import re_path, reverse
from django.utils.safestring import mark_safe

# Standard Library
import os
from datetime import date, timedelta

# Third Party
from reversion.admin import VersionAdmin

# MuckRock
from muckrock.agency.models import Agency
from muckrock.communication.admin import (
    EmailCommunicationInline,
    FaxCommunicationInline,
    MailCommunicationInline,
    PortalCommunicationInline,
    WebCommunicationInline,
)
from muckrock.communication.models import EmailAddress, PhoneNumber
from muckrock.core import autocomplete
from muckrock.foia.models import (
    CommunicationMoveLog,
    FOIACommunication,
    FOIAComposer,
    FOIAFile,
    FOIANote,
    FOIARequest,
    FOIATemplate,
    FOIALog,
    OutboundComposerAttachment,
    OutboundRequestAttachment,
    TrackingNumber,
)
from muckrock.foia.tasks import (
    autoimport,
    noindex_documentcloud,
    set_document_cloud_pages,
    upload_document_cloud,
)
from muckrock.jurisdiction.models import Jurisdiction


class FOIAFileAdminForm(forms.ModelForm):
    """Form to validate document only has ASCII characters in it"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clean_title = self._validate("title")
        self.clean_source = self._validate("source")
        self.clean_description = self._validate("description")

    class Meta:
        model = FOIAFile
        fields = "__all__"

    @staticmethod
    def _only_ascii(text):
        """Ensure's that text only contains ASCII characters"""
        non_ascii = "".join(c for c in text if ord(c) >= 128)
        if non_ascii:
            raise forms.ValidationError(
                "Field contains non-ASCII characters: %s" % non_ascii
            )

    def _validate(self, field):
        """Make a validator for field"""

        def inner():
            """Ensure field only has ASCII characters"""
            data = self.cleaned_data[field]
            self._only_ascii(data)
            return data

        return inner


class FOIAFileInline(admin.StackedInline):
    """FOIA File Inline admin options"""

    model = FOIAFile
    form = FOIAFileAdminForm
    readonly_fields = ("doc_id", "pages", "access", "source")
    fields = (
        ("title", "datetime"),
        "ffile",
        "description",
        ("doc_id", "pages"),
        ("source", "access"),
    )
    extra = 0


class CommunicationMoveLogInline(admin.TabularInline):
    """Communication Move Log inline"""

    model = CommunicationMoveLog
    readonly_fields = ("datetime", "user", "foia_link")
    fields = ("datetime", "user", "foia_link")
    extra = 0

    @mark_safe
    def foia_link(self, obj):
        """Link to the FOIA"""
        link = reverse("admin:foia_foiarequest_change", args=(obj.foia.pk,))
        return '<a href="%s">%s</a>' % (link, obj.foia.title)

    foia_link.short_description = "From FOIA Request"


class FOIACommunicationAdminForm(forms.ModelForm):
    """Form for comm inline"""

    from_user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2(
            url="user-autocomplete",
            attrs={"data-placeholder": "User?", "data-width": None},
        ),
    )
    to_user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2(
            url="user-autocomplete",
            attrs={"data-placeholder": "User?", "data-width": None},
        ),
    )

    class Meta:
        model = FOIACommunication
        fields = "__all__"


class FOIACommunicationAdmin(VersionAdmin):
    """FOIA Communication admin options"""

    model = FOIACommunication
    form = FOIACommunicationAdminForm
    readonly_fields = ("foia_link", "confirmed")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "foia_link",
                    ("from_user", "to_user"),
                    ("subject", "datetime"),
                    "communication",
                    "status",
                    "response",
                    "autogenerated",
                    "thanks",
                    "full_html",
                    "hidden",
                    "download",
                )
            },
        ),
        (
            "Deprecated",
            {
                "classes": ("collapse",),
                "fields": (
                    "from_who",
                    "to_who",
                    "priv_from_who",
                    "priv_to_who",
                    "delivered",
                    "fax_id",
                ),
                "description": "These values are no longer actively used.  "
                "They are here to view on old data only.  If you find yourself "
                "needing to look here often, something is probably wrong and "
                "you should file a bug",
            },
        ),
    )
    inlines = (
        FOIAFileInline,
        EmailCommunicationInline,
        FaxCommunicationInline,
        MailCommunicationInline,
        WebCommunicationInline,
        PortalCommunicationInline,
        CommunicationMoveLogInline,
    )

    @mark_safe
    def foia_link(self, obj):
        """Link to this communication's FOIA admin"""
        link = reverse("admin:foia_foiarequest_change", args=(obj.foia.pk,))
        return '<a href="%s">%s</a>' % (link, obj.foia.title)

    foia_link.short_description = "FOIA Request"

    @transaction.atomic
    def save_formset(self, request, form, formset, change):
        """Actions to take while saving inline files"""

        if formset.model != FOIAFile:
            super().save_formset(request, form, formset, change)
            return

        instances = formset.save(commit=False)
        for instance in instances:
            # only way to tell if its new or not is to check the db
            change = True
            try:
                formset.model.objects.get(pk=instance.pk)
            except formset.model.DoesNotExist:
                change = False

            instance.save()
            # its new, so notify the user about it
            if not change:
                instance.comm.foia.update(instance.anchor())

            transaction.on_commit(
                lambda instance=instance: upload_document_cloud.delay(instance.pk)
            )

        formset.save_m2m()

        for obj in formset.deleted_objects:
            obj.delete()


class FOIACommunicationInline(admin.StackedInline):
    """FOIA Communication Inline admin options"""

    model = FOIACommunication
    fk_name = "foia"
    extra = 1
    readonly_fields = (
        "get_delivered",
        "confirmed_datetime",
        "error",
        "file_count",
        "file_names",
        "open",
    )
    show_change_link = True
    form = FOIACommunicationAdminForm
    fields = (
        ("from_user", "to_user"),
        ("subject", "datetime"),
        "communication",
        ("file_count", "file_names"),
        "status",
        "get_delivered",
        ("confirmed_datetime", "open", "error"),
        ("response", "autogenerated", "thanks", "full_html", "hidden", "download"),
    )

    def file_count(self, instance):
        """File count for this communication"""
        return instance.files_count

    def file_names(self, instance):
        """All file's names for this communication"""
        return "\n".join(os.path.basename(f.ffile.name) for f in instance.display_files)

    def confirmed_datetime(self, instance):
        """Date time when this was confirmed as being sent"""
        if instance.email_confirmed_datetime:
            return instance.email_confirmed_datetime
        elif instance.fax_confirmed_datetime:
            return instance.fax_confirmed_datetime
        else:
            return None

    def open(self, instance):
        """Was this communicaion opened?"""
        return instance.opens_count > 0

    open.boolean = True

    def error(self, instance):
        """Did this communication have an error sending?"""
        return instance.email_errors_count > 0 or instance.fax_errors_count > 0

    error.boolean = True

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .preload_files(limit=20)
            .prefetch_related("emails", "faxes", "mails", "web_comms", "portals")
            .annotate(
                files_count=Count("files"),
                opens_count=Count("emails__opens"),
                email_errors_count=Count("emails__errors"),
                fax_errors_count=Count("faxes__errors"),
                email_confirmed_datetime=Max("emails__confirmed_datetime"),
                fax_confirmed_datetime=Max("faxes__confirmed_datetime"),
            )
        )


class FOIANoteAdminForm(forms.ModelForm):
    """Form for note inline"""

    author = forms.ModelChoiceField(
        label="Author",
        queryset=User.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="user-autocomplete",
            attrs={"data-placeholder": "User?", "data-width": None},
        ),
    )

    class Meta:
        model = FOIANote
        fields = "__all__"


class FOIANoteInline(admin.TabularInline):
    """FOIA Notes Inline admin options"""

    model = FOIANote
    form = FOIANoteAdminForm
    extra = 1


class TrackingNumberInline(admin.TabularInline):
    """Tracking Number Inline admin options"""

    model = TrackingNumber
    extra = 1


class FOIARequestAdminForm(forms.ModelForm):
    """Form to include custom choice fields"""

    agency = forms.ModelChoiceField(
        queryset=Agency.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="agency-autocomplete",
            attrs={"data-placeholder": "Agency?", "data-width": None},
        ),
    )
    read_collaborators = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url="user-autocomplete",
            attrs={"data-placeholder": "User?", "data-width": None},
        ),
    )
    edit_collaborators = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url="user-autocomplete",
            attrs={"data-placeholder": "User?", "data-width": None},
        ),
    )
    email = forms.ModelChoiceField(
        queryset=EmailAddress.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2(
            url="email-autocomplete",
            attrs={
                "data-placeholder": "Email?",
                "data-width": None,
                "data-html": False,
            },
        ),
    )
    fax = forms.ModelChoiceField(
        queryset=PhoneNumber.objects.filter(type="fax"),
        required=False,
        widget=autocomplete.ModelSelect2(
            url="fax-autocomplete",
            attrs={
                "data-placeholder": "Fax Number?",
                "data-width": None,
                "data-html": False,
            },
        ),
    )
    cc_emails = forms.ModelMultipleChoiceField(
        queryset=EmailAddress.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url="email-autocomplete",
            attrs={
                "data-placeholder": "Emails?",
                "data-width": None,
                "data-html": False,
            },
        ),
    )
    proxy = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2(
            url="user-autocomplete",
            attrs={"data-placeholder": "User?", "data-width": None},
        ),
    )

    class Meta:
        model = FOIARequest
        fields = "__all__"


class FOIARequestAdmin(VersionAdmin):
    """FOIA Request admin options"""

    change_list_template = "admin/foia/foiarequest/change_list.html"
    prepopulated_fields = {"slug": ("title",)}
    list_display = ("title", "get_user", "status", "agency", "get_jurisdiction")
    list_filter = ["status"]
    list_select_related = ("agency__jurisdiction", "composer__user")
    search_fields = ["title", "tracking_ids__tracking_id", "mail_id"]
    readonly_fields = ["composer_link", "get_user", "mail_id"]
    inlines = [TrackingNumberInline, FOIACommunicationInline, FOIANoteInline]
    save_on_top = True
    form = FOIARequestAdminForm
    exclude = ["composer"]
    autocomplete_fields = ["address", "crowdfund", "portal"]

    def get_user(self, obj):
        """Get the user"""
        return obj.composer.user

    get_user.short_description = "User"
    get_user.admin_order_field = "composer__user"

    @mark_safe
    def composer_link(self, obj):
        """Link to the Composer"""
        link = reverse("admin:foia_foiacomposer_change", args=(obj.composer.pk,))
        return '<a href="%s">%s</a>' % (link, obj.composer.title)

    composer_link.short_description = "Composer"

    def get_jurisdiction(self, obj):
        """Get the jurisdiction"""
        return obj.agency.jurisdiction

    get_jurisdiction.short_description = "Jurisdiction"
    get_jurisdiction.admin_order_field = "agency__jurisdiction"

    def save_model(self, request, obj, form, change):
        """Actions to take when a request is saved from the admin"""

        # If changing to completed and embargoed, set embargo date to 30 days out
        if obj.status in ["done", "partial"] and obj.embargo and not obj.date_embargo:
            obj.date_embargo = date.today() + timedelta(30)

        # If turned noindex on, turn noindex on DocumentCloud as well
        if "noindex" in form.changed_data and form.cleaned_data["noindex"]:
            noindex_documentcloud.delay(obj.pk)

        # NOT saving here if changed
        # saving after formset so that we can check for updates there first
        if not change:
            obj.save()

    def save_formset(self, request, form, formset, change):
        """Actions to take while saving inline instances"""

        if formset.model == FOIANote:
            formset.save()
            # check for foia updates here so that communication updates take priority
            # (Notes are last)
            foia = form.instance
            old_foia = FOIARequest.objects.get(pk=foia.pk)
            if foia.status != old_foia.status:
                foia.update()
            foia.update_dates()
            foia.save()
        # check communications for new ones to notify the user of an update
        elif formset.model == FOIACommunication:
            instances = formset.save(commit=False)
            for instance in instances:
                # only way to tell if its new or not is to check the db
                change = True
                try:
                    formset.model.objects.get(pk=instance.pk)
                except formset.model.DoesNotExist:
                    change = False

                instance.save()
                # its new, so notify the user about it
                if not change:
                    instance.foia.update(instance.anchor())

            for instance in formset.deleted_objects:
                instance.delete()

            formset.save_m2m()
        else:
            formset.save()

    def get_urls(self):
        """Add custom URLs here"""
        urls = super().get_urls()
        my_urls = [
            re_path(
                r"^send_update/(?P<idx>\d+)/$",
                self.admin_site.admin_view(self.send_update),
                name="foia-admin-send-update",
            ),
            re_path(
                r"^retry_pages/(?P<idx>\d+)/$",
                self.admin_site.admin_view(self.retry_pages),
                name="foia-admin-retry-pages",
            ),
            re_path(
                r"^autoimport/$",
                self.admin_site.admin_view(self.autoimport),
                name="foia-admin-autoimport",
            ),
        ]
        return my_urls + urls

    def send_update(self, request, idx):
        """Manually send the user an update notification"""

        foia = get_object_or_404(FOIARequest, pk=idx)
        foia.update()
        messages.info(
            request, "An update notification has been set to the user, %s" % foia.user
        )
        return HttpResponseRedirect(
            reverse("admin:foia_foiarequest_change", args=[foia.pk])
        )

    def retry_pages(self, request, idx):
        """Retry getting the page count"""

        docs = FOIAFile.objects.filter(foia=idx, pages=0).get_doccloud()
        for doc in docs:
            set_document_cloud_pages.delay(doc.pk)

        messages.info(
            request,
            "Attempting to set the page count for %d documents... Please "
            "wait while the Document Cloud servers are being accessed" % docs.count(),
        )
        return HttpResponseRedirect(
            reverse("admin:foia_foiarequest_change", args=[idx])
        )

    def autoimport(self, request):
        """Autoimport documents from S3"""
        autoimport.apply_async()
        messages.info(request, "Auotimport started")
        return HttpResponseRedirect(reverse("admin:foia_foiarequest_changelist"))


class FOIARequestInline(admin.TabularInline):
    """FOIA Request Inline admin options"""

    model = FOIARequest
    extra = 0
    show_change_link = True
    readonly_fields = ("title", "status", "agency", "get_jurisdiction")
    fields = ("title", "status", "agency", "get_jurisdiction")

    def get_jurisdiction(self, obj):
        """Get the jurisdiction from the agency"""
        return obj.agency.jurisdiction

    get_jurisdiction.short_description = "Jurisdiction"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("agency__jurisdiction")


class FOIAComposerAdminForm(forms.ModelForm):
    """Form for the FOIA composer admin"""

    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="user-autocomplete",
            attrs={"data-placeholder": "User?", "data-width": None},
        ),
    )
    agencies = forms.ModelMultipleChoiceField(
        queryset=Agency.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2Multiple(
            url="agency-autocomplete",
            attrs={"data-placeholder": "Agency?", "data-width": None},
        ),
    )

    class Meta:
        model = FOIAComposer
        fields = "__all__"


class FOIAComposerAdmin(VersionAdmin):
    """FOIA Composer admin options"""

    prepopulated_fields = {"slug": ("title",)}
    list_display = ("title", "user", "status")
    search_fields = ["title", "requested_docs"]
    autocomplete_fields = ["organization", "parent"]
    form = FOIAComposerAdminForm
    inlines = [FOIARequestInline]


class OutboundRequestAttachmentAdminForm(forms.ModelForm):
    """Form for outbound attachment admin"""

    foia = forms.ModelChoiceField(
        queryset=FOIARequest.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="foia-request-autocomplete",
            attrs={"data-placeholder": "FOIA?", "data-width": None},
        ),
    )
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="user-autocomplete",
            attrs={"data-placeholder": "User?", "data-width": None},
        ),
    )

    class Meta:
        model = OutboundRequestAttachment
        fields = "__all__"


class OutboundRequestAttachmentAdmin(VersionAdmin):
    """Outbound Attachment admin options"""

    search_fields = ("foia__title", "user__username")
    list_display = ("foia", "user", "ffile", "date_time_stamp")
    list_select_related = ("foia", "user")
    date_hierarchy = "date_time_stamp"
    form = OutboundRequestAttachmentAdminForm


class OutboundComposerAttachmentAdminForm(forms.ModelForm):
    """Form for outbound attachment admin"""

    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="user-autocomplete",
            attrs={"data-placeholder": "User?", "data-width": None},
        ),
    )

    class Meta:
        model = OutboundComposerAttachment
        fields = "__all__"


class OutboundComposerAttachmentAdmin(VersionAdmin):
    """Outbound Attachment admin options"""

    search_fields = ("composer__title", "user__username")
    list_display = ("composer", "user", "ffile", "date_time_stamp")
    list_select_related = ("composer", "user")
    date_hierarchy = "date_time_stamp"
    autocomplete_fields = ["composer"]
    form = OutboundComposerAttachmentAdminForm


class FOIATemplateAdminForm(forms.ModelForm):
    """Form for the FOIA template admin"""

    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="user-autocomplete",
            attrs={"data-placeholder": "User?", "data-width": None},
        ),
    )
    jurisdiction = forms.ModelChoiceField(
        queryset=Jurisdiction.objects.filter(hidden=False),
        required=False,
        widget=autocomplete.ModelSelect2(
            url="jurisdiction-autocomplete",
            attrs={"data-placeholder": "Jurisdiction?", "data-width": None},
        ),
    )

    class Meta:
        model = FOIATemplate
        fields = "__all__"


class FOIATemplateAdmin(VersionAdmin):
    """FOIA Template admin"""

    list_display = ("name", "user", "jurisdiction")
    search_fields = ["name", "template"]
    form = FOIATemplateAdminForm

class FOIALogAdminForm(forms.ModelForm):
    """Form for FOIA Log admin"""

    agency = forms.ModelChoiceField(
        queryset=Agency.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="agency-autocomplete",
            attrs={"data-placeholder": "Agency?", "data-width": None},
        ),
    )

    class Meta:
        model = FOIALog
        fields = "__all__"

class FOIALogAdmin(VersionAdmin):
    """Outbound Attachment admin options"""
    list_display = ("agency", "request_id", "date")
    search_fields = ["request_id", "agency"]
    form = FOIALogAdminForm

admin.site.register(FOIARequest, FOIARequestAdmin)
admin.site.register(FOIACommunication, FOIACommunicationAdmin)
admin.site.register(FOIAComposer, FOIAComposerAdmin)
admin.site.register(FOIATemplate, FOIATemplateAdmin)
admin.site.register(FOIALog, FOIALogAdmin)
admin.site.register(OutboundRequestAttachment, OutboundRequestAttachmentAdmin)
admin.site.register(OutboundComposerAttachment, OutboundComposerAttachmentAdmin)
