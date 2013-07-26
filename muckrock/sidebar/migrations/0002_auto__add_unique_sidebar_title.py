# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding unique constraint on 'Sidebar', fields ['title']
        db.create_unique('sidebar_sidebar', ['title'])
    
    
    def backwards(self, orm):
        
        # Removing unique constraint on 'Sidebar', fields ['title']
        db.delete_unique('sidebar_sidebar', ['title'])
    
    
    models = {
        'sidebar.sidebar': {
            'Meta': {'object_name': 'Sidebar'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        }
    }
    
    complete_apps = ['sidebar']
