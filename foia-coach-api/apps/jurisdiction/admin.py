"""Django admin configuration for jurisdiction app."""
from django.contrib import admin
from .models import (
    ExampleResponse,
    JurisdictionResource,
    NFOICPartner,
    ResourceProviderUpload,
)


class ResourceProviderUploadInline(admin.TabularInline):
    """
    Inline admin for ResourceProviderUpload model.

    Adding a new provider here will automatically trigger an upload
    (status defaults to 'pending' which triggers the upload signal).
    """

    model = ResourceProviderUpload
    extra = 0  # Don't show blank forms by default
    readonly_fields = [
        'provider_file_id',
        'provider_store_id',
        'index_status',
        'indexed_at',
        'error_message',
        'created_at',
        'updated_at'
    ]
    fields = [
        'provider',
        'index_status',
        'indexed_at',
        'error_message'
    ]
    can_delete = True
    verbose_name = "Provider Upload"
    verbose_name_plural = "Provider Uploads"

    def has_add_permission(self, request, obj=None):
        """Allow manual creation of upload records."""
        return True


@admin.register(JurisdictionResource)
class JurisdictionResourceAdmin(admin.ModelAdmin):
    """Admin interface for JurisdictionResource model."""

    list_display = [
        'display_name',
        'jurisdiction_abbrev',
        'resource_type',
        'upload_status_summary',
        'is_active',
        'created_at'
    ]
    list_filter = ['resource_type', 'is_active', 'jurisdiction_abbrev']
    search_fields = ['display_name', 'jurisdiction_abbrev', 'description']
    readonly_fields = [
        'gemini_file_id',
        'gemini_display_name',
        'created_at',
        'updated_at'
    ]
    inlines = [ResourceProviderUploadInline]

    fieldsets = (
        ('Jurisdiction Information', {
            'fields': ('jurisdiction_id', 'jurisdiction_abbrev')
        }),
        ('Resource Details', {
            'fields': ('display_name', 'description', 'resource_type', 'file', 'order', 'is_active')
        }),
        ('Legacy Fields (Deprecated)', {
            'fields': ('gemini_file_id', 'gemini_display_name'),
            'classes': ('collapse',),
            'description': 'Deprecated fields kept for backward compatibility. Use ResourceProviderUpload instead.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def upload_status_summary(self, obj):
        """
        Display upload status across all providers.

        Returns a formatted string showing the status for each provider.
        """
        statuses = obj.get_upload_summary()
        if not statuses:
            return "No uploads"

        # Format as "openai: ready | gemini: pending"
        status_strs = [f"{provider}: {status}" for provider, status in statuses.items()]
        return " | ".join(status_strs)

    upload_status_summary.short_description = "Provider Upload Status"


@admin.register(ExampleResponse)
class ExampleResponseAdmin(admin.ModelAdmin):
    """Admin interface for ExampleResponse model."""

    list_display = [
        'title',
        'jurisdiction_abbrev_display',
        'is_active',
        'order',
        'updated_at',
    ]
    list_filter = ['is_active', 'jurisdiction_abbrev']
    search_fields = ['title', 'user_question', 'assistant_response']
    list_editable = ['is_active', 'order']
    fieldsets = (
        (None, {
            'fields': ('title', 'jurisdiction_abbrev', 'order', 'is_active')
        }),
        ('Example Q&A', {
            'fields': ('user_question', 'assistant_response'),
        }),
    )

    def jurisdiction_abbrev_display(self, obj):
        return obj.jurisdiction_abbrev or "Global"
    jurisdiction_abbrev_display.short_description = "Scope"


@admin.register(NFOICPartner)
class NFOICPartnerAdmin(admin.ModelAdmin):
    """Admin interface for NFOICPartner model."""

    list_display = [
        'name',
        'jurisdiction_abbrev',
        'website',
        'is_active',
        'order',
        'updated_at',
    ]
    list_editable = ['is_active', 'order']
    list_filter = ['is_active', 'jurisdiction_abbrev']
    search_fields = ['name', 'jurisdiction_abbrev', 'email', 'description']
    fieldsets = (
        (None, {
            'fields': ('name', 'jurisdiction_abbrev', 'order', 'is_active')
        }),
        ('Contact Information', {
            'fields': ('website', 'email', 'phone'),
        }),
        ('Details', {
            'fields': ('description',),
        }),
    )
