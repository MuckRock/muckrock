# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Sidebar'
        db.create_table('sidebar_sidebar', (
            ('text', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('sidebar', ['Sidebar'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Sidebar'
        db.delete_table('sidebar_sidebar')
    
    
    models = {
        'sidebar.sidebar': {
            'Meta': {'object_name': 'Sidebar'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }
    
    complete_apps = ['sidebar']
