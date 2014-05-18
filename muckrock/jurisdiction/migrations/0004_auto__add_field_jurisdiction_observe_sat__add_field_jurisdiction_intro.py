# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    depends_on = (
        ('business_days', '0001_initial'),
    )
    
    def forwards(self, orm):
        
        # Adding field 'Jurisdiction.observe_sat'
        db.add_column('jurisdiction_jurisdiction', 'observe_sat', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True), keep_default=False)

        # Adding field 'Jurisdiction.intro'
        db.add_column('jurisdiction_jurisdiction', 'intro', self.gf('django.db.models.fields.TextField')(default='', blank=True), keep_default=False)

        # Adding field 'Jurisdiction.waiver'
        db.add_column('jurisdiction_jurisdiction', 'waiver', self.gf('django.db.models.fields.TextField')(default='', blank=True), keep_default=False)

        # Adding M2M table for field holidays on 'Jurisdiction'
        db.create_table('jurisdiction_jurisdiction_holidays', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('jurisdiction', models.ForeignKey(orm['jurisdiction.jurisdiction'], null=False)),
            ('holiday', models.ForeignKey(orm['business_days.holiday'], null=False))
        ))
        db.create_unique('jurisdiction_jurisdiction_holidays', ['jurisdiction_id', 'holiday_id'])

        # Changing field 'Jurisdiction.image'
        db.alter_column('jurisdiction_jurisdiction', 'image', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True))
    
    
    def backwards(self, orm):
        
        # Deleting field 'Jurisdiction.observe_sat'
        db.delete_column('jurisdiction_jurisdiction', 'observe_sat')

        # Deleting field 'Jurisdiction.intro'
        db.delete_column('jurisdiction_jurisdiction', 'intro')

        # Deleting field 'Jurisdiction.waiver'
        db.delete_column('jurisdiction_jurisdiction', 'waiver')

        # Removing M2M table for field holidays on 'Jurisdiction'
        db.delete_table('jurisdiction_jurisdiction_holidays')

        # Changing field 'Jurisdiction.image'
        db.alter_column('jurisdiction_jurisdiction', 'image', self.gf('django.db.models.fields.files.ImageField')())
    
    
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
        },
        'jurisdiction.jurisdiction': {
            'Meta': {'object_name': 'Jurisdiction'},
            'abbrev': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True'}),
            'days': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'holidays': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['business_days.Holiday']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'image_attr_line': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'intro': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'level': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'observe_sat': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['jurisdiction.Jurisdiction']"}),
            'public_notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '55', 'db_index': 'True'}),
            'waiver': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        }
    }
    
    complete_apps = ['jurisdiction']
