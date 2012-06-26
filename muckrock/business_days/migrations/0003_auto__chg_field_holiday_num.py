# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Changing field 'Holiday.num'
        db.alter_column('business_days_holiday', 'num', self.gf('django.db.models.fields.SmallIntegerField')(null=True))
    
    
    def backwards(self, orm):
        
        # Changing field 'Holiday.num'
        db.alter_column('business_days_holiday', 'num', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True))
    
    
    models = {
        'business_days.holiday': {
            'Meta': {'object_name': 'Holiday'},
            'day': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'month': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'num': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True'}),
            'weekday': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'})
        }
    }
    
    complete_apps = ['business_days']
