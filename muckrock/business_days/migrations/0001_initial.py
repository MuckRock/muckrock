# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Holiday'
        db.create_table('business_days_holiday', (
            ('kind', self.gf('django.db.models.fields.CharField')(max_length=8)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('month', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('num', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('weekday', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('day', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
        ))
        db.send_create_signal('business_days', ['Holiday'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Holiday'
        db.delete_table('business_days_holiday')
    
    
    models = {
        'business_days.holiday': {
            'Meta': {'object_name': 'Holiday'},
            'day': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'month': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'num': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'weekday': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        }
    }
    
    complete_apps = ['business_days']
