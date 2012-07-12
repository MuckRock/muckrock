# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Deleting model 'RodeoOption'
        db.delete_table('rodeo_rodeooption')

        # Deleting model 'RodeoVote'
        db.delete_table('rodeo_rodeovote')

        # Deleting model 'Rodeo'
        db.delete_table('rodeo_rodeo')
    
    
    def backwards(self, orm):
        
        # Adding model 'RodeoOption'
        db.create_table('rodeo_rodeooption', (
            ('rodeo', self.gf('django.db.models.fields.related.ForeignKey')(related_name='options', to=orm['rodeo.Rodeo'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=70)),
        ))
        db.send_create_signal('rodeo', ['RodeoOption'])

        # Adding model 'RodeoVote'
        db.create_table('rodeo_rodeovote', (
            ('page', self.gf('django.db.models.fields.IntegerField')()),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
            ('option', self.gf('django.db.models.fields.related.ForeignKey')(related_name='votes', to=orm['rodeo.RodeoOption'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('rodeo', ['RodeoVote'])

        # Adding model 'Rodeo'
        db.create_table('rodeo_rodeo', (
            ('document', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['foia.FOIADocument'])),
            ('question', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=70)),
        ))
        db.send_create_signal('rodeo', ['Rodeo'])
    
    
    models = {
        
    }
    
    complete_apps = ['rodeo']
