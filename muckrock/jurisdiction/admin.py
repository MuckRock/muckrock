"""
Admin registration for Jurisdiction models
"""

from django.contrib import admin

from adaptor.model import CsvModel
from adaptor.fields import CharField, DjangoModelField

#from jurisdiction.models import Jurisdiction
from foia.models import Jurisdiction

# These inhereit more than the allowed number of public methods
# pylint: disable=R0904

class JurisdictionAdmin(admin.ModelAdmin):
    """Jurisdiction admin options"""
    list_display = ('name', 'level')
    list_filter = ['level']
    search_fields = ['name']
    filter_horizontal = ('holidays', )
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'abbrev', 'level', 'parent', 'hidden', 'image',
                       'image_attr_line', 'public_notes')
        }),
        ('Options for states/federal', {
            'classes': ('collapse',),
            'fields': ('days', 'observe_sat', 'holidays', 'intro', 'waiver')
        }),
    )

admin.site.register(Jurisdiction, JurisdictionAdmin)


class JurisdictionCsvModel(CsvModel):
    """CSV import model for jurisdictions"""

    name = CharField()
    slug = CharField()
    level = CharField(transform=lambda x: x.lower()[0])
    parent = DjangoModelField(Jurisdiction, pk='name')

    class Meta:
        # pylint: disable=R0903
        dbModel = Jurisdiction
        delimiter = ','
