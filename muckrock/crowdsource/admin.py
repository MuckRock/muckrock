# -*- coding: utf-8 -*-
"""Admin configuration for the crowdsource app"""

from django import forms
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from autocomplete_light import shortcuts as autocomplete_light

from muckrock.crowdsource.models import (
        Crowdsource,
        CrowdsourceData,
        CrowdsourceField,
        CrowdsourceChoice,
        CrowdsourceResponse,
        CrowdsourceValue,
        )


class CrowdsourceAdminForm(forms.ModelForm):
    """Form for Crowdsource admin"""

    user = autocomplete_light.ModelChoiceField(
            'UserAutocomplete',
            queryset=User.objects.all(),
            )

    class Meta:
        model = Crowdsource
        fields = '__all__'


class CrowdsourceResponseAdminForm(forms.ModelForm):
    """Form for Crowdsource response admin"""

    user = autocomplete_light.ModelChoiceField(
            'UserAutocomplete',
            queryset=User.objects.all(),
            )

    class Meta:
        model = CrowdsourceResponse
        fields = '__all__'


class CrowdsourceDataInline(admin.TabularInline):
    """Crowdsource Data inline options"""
    model = CrowdsourceData


class CrowdsourceFieldInline(admin.TabularInline):
    """Crowdsource Field inline options"""
    model = CrowdsourceField
    show_change_link = True


class CrowdsourceResponseInline(admin.TabularInline):
    """Crowdsource Response inline options"""
    model = CrowdsourceResponse
    form = CrowdsourceResponseAdminForm
    show_change_link = True
    readonly_fields = ('data',)


@admin.register(Crowdsource)
class CrowdsourceAdmin(admin.ModelAdmin):
    """Crowdsource admin options"""
    form = CrowdsourceAdminForm
    prepopulated_fields = {'slug': ('title',)}
    inlines = (
            CrowdsourceDataInline,
            CrowdsourceFieldInline,
            CrowdsourceResponseInline,
            )


class CrowdsourceChoiceInline(admin.TabularInline):
    """Crowdsource Choice inline options"""
    model = CrowdsourceChoice


@admin.register(CrowdsourceField)
class CrowdsourceFieldAdmin(admin.ModelAdmin):
    """Crowdsource field options"""
    inlines = (
            CrowdsourceChoiceInline,
            )
    fields = (
            'cs_link',
            'label',
            'type',
            'order',
            )
    readonly_fields = ('cs_link',)

    def cs_link(self, obj):
        """Link back to the crowdsource page"""
        # pylint: disable=no-self-use
        link = reverse(
                'admin:crowdsource_crowdsource_change',
                args=(obj.crowdsource.pk,),
                )
        return '<a href="{}">{}</a>'.format(link, obj.crowdsource.title)
    cs_link.allow_tags = True
    cs_link.short_description = 'Crowdsource'


class CrowdsourceValueInline(admin.TabularInline):
    """Crowdsource Value inline options"""
    model = CrowdsourceValue


@admin.register(CrowdsourceResponse)
class CrowdsourceResponseAdmin(admin.ModelAdmin):
    """Crowdsource response options"""
    form = CrowdsourceResponseAdminForm
    inlines = (
            CrowdsourceValueInline,
            )
    fields = (
            'cs_link',
            'user',
            'datetime',
            'data',
            )
    readonly_fields = ('cs_link', 'data')

    def cs_link(self, obj):
        """Link back to the crowdsource page"""
        # pylint: disable=no-self-use
        link = reverse(
                'admin:crowdsource_crowdsource_change',
                args=(obj.crowdsource.pk,),
                )
        return '<a href="{}">{}</a>'.format(link, obj.crowdsource.title)
    cs_link.allow_tags = True
    cs_link.short_description = 'Crowdsource'
