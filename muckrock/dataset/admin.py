# -*- coding: utf-8 -*-
"""
Admin for data set application
"""

from django.contrib import admin

from reversion.admin import VersionAdmin

from muckrock.dataset.models import (
        DataSet,
        DataField,
        )


class DataFieldInline(admin.TabularInline):
    """Inline for a data field"""
    model = DataField
    prepopulated_fields = {'slug': ('name',)}
    extra = 0


class DataSetAdmin(VersionAdmin):
    """Admin for a data set"""
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'user', 'created_datetime')
    date_hieracrhy = 'created_datetime'
    search_fields = ('name',)
    readonly_fields = ('created_datetime',)
    inlines = [DataFieldInline]


admin.site.register(DataSet, DataSetAdmin)
