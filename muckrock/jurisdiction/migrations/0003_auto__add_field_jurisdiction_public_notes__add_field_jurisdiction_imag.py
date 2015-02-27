# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding field 'Jurisdiction.public_notes'
        db.add_column('jurisdiction_jurisdiction', 'public_notes', self.gf('django.db.models.fields.TextField')(default='', blank=True), keep_default=False)

        # Adding field 'Jurisdiction.image'
        db.add_column('jurisdiction_jurisdiction', 'image', self.gf('django.db.models.fields.files.ImageField')(null=True), keep_default=False)

        # Adding field 'Jurisdiction.image_attr_line'
        db.add_column('jurisdiction_jurisdiction', 'image_attr_line', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True), keep_default=False)


    def backwards(self, orm):

        # Deleting field 'Jurisdiction.public_notes'
        db.delete_column('jurisdiction_jurisdiction', 'public_notes')

        # Deleting field 'Jurisdiction.image'
        db.delete_column('jurisdiction_jurisdiction', 'image')

        # Deleting field 'Jurisdiction.image_attr_line'
        db.delete_column('jurisdiction_jurisdiction', 'image_attr_line')


    models = {
        'jurisdiction.jurisdiction': {
            'Meta': {'object_name': 'Jurisdiction'},
            'abbrev': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True'}),
            'days': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {}),
            'image_attr_line': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'level': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['jurisdiction.Jurisdiction']"}),
            'public_notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '55', 'db_index': 'True'})
        }
    }

    complete_apps = ['jurisdiction']
