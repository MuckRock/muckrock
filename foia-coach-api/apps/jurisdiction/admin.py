"""Django admin configuration for jurisdiction app."""
from django.contrib import admin
from .models import JurisdictionResource


@admin.register(JurisdictionResource)
class JurisdictionResourceAdmin(admin.ModelAdmin):
    """Admin interface for JurisdictionResource model."""

    list_display = [
        'display_name',
        'jurisdiction_abbrev',
        'resource_type',
        'index_status',
        'is_active',
        'created_at'
    ]
    list_filter = ['resource_type', 'index_status', 'is_active', 'jurisdiction_abbrev']
    search_fields = ['display_name', 'jurisdiction_abbrev', 'description']
    readonly_fields = [
        'gemini_file_id',
        'gemini_display_name',
        'indexed_at',
        'index_status',
        'created_at',
        'updated_at'
    ]
    fieldsets = (
        ('Jurisdiction Information', {
            'fields': ('jurisdiction_id', 'jurisdiction_abbrev')
        }),
        ('Resource Details', {
            'fields': ('display_name', 'description', 'resource_type', 'file', 'order', 'is_active')
        }),
        ('Gemini Integration', {
            'fields': ('gemini_file_id', 'gemini_display_name', 'index_status', 'indexed_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
