# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from django.core import management

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Jurisdiction'
        db.create_table('foia_jurisdiction', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='children', null=True, to=orm['foia.Jurisdiction'])),
            ('level', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('abbrev', self.gf('django.db.models.fields.CharField')(max_length=5, blank=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=55, db_index=True)),
        ))
        db.send_create_signal('foia', ['Jurisdiction'])

        # Adding model 'AgencyType'
        db.create_table('foia_agencytype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=60)),
        ))
        db.send_create_signal('foia', ['AgencyType'])

        # Adding model 'Agency'
        db.create_table('foia_agency', (
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True)),
            ('jurisdiction', self.gf('django.db.models.fields.related.ForeignKey')(related_name='agencies', to=orm['foia.Jurisdiction'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('address', self.gf('django.db.models.fields.TextField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=60)),
        ))
        db.send_create_signal('foia', ['Agency'])

        # Adding M2M table for field types on 'Agency'
        db.create_table('foia_agency_types', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('agency', models.ForeignKey(orm['foia.agency'], null=False)),
            ('agencytype', models.ForeignKey(orm['foia.agencytype'], null=False))
        ))
        db.create_unique('foia_agency_types', ['agency_id', 'agencytype_id'])

        # Adding field 'FOIARequest.agency_type'
        db.add_column('foia_foiarequest', 'agency_type', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['foia.AgencyType']), keep_default=False)

        # Adding field 'FOIARequest.jurisdiction_new'
        db.add_column('foia_foiarequest', 'jurisdiction_new', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['foia.Jurisdiction']), keep_default=False)

        # With new tables created, load the fixtures so we can migrate the data
        management.call_command('loaddata', 'jurisdictions.json')
        management.call_command('loaddata', 'agency_types.json')

        # migrate the data
        for foia in orm.FOIARequest.objects.all():
            foia.jurisdiction_new = orm.Jurisdiction.objects.get(slug=foia.jurisdiction)
            foia.agency_type = orm.AgencyType.objects.get(name=foia.agency)
            foia.save()
    
    
    def backwards(self, orm):

        # migrate the data
        for foia in orm.FOIARequest.objects.all():
            foia.jurisdiction = foia.jurisdiction_new.slug
            foia.agency = foia.agency_type.name
            foia.save()
        
        # Deleting model 'Jurisdiction'
        db.delete_table('foia_jurisdiction')

        # Deleting model 'AgencyType'
        db.delete_table('foia_agencytype')

        # Deleting model 'Agency'
        db.delete_table('foia_agency')

        # Removing M2M table for field types on 'Agency'
        db.delete_table('foia_agency_types')

        # Deleting field 'FOIARequest.agency_type'
        db.delete_column('foia_foiarequest', 'agency_type_id')

        # Deleting field 'FOIARequest.jurisdiction_new'
        db.delete_column('foia_foiarequest', 'jurisdiction_new_id')
    
    
    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'foia.agency': {
            'Meta': {'object_name': 'Agency'},
            'address': ('django.db.models.fields.TextField', [], {}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jurisdiction': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'agencies'", 'to': "orm['foia.Jurisdiction']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'types': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['foia.AgencyType']", 'symmetrical': 'False'})
        },
        'foia.agencytype': {
            'Meta': {'object_name': 'AgencyType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'})
        },
        'foia.foiafile': {
            'Meta': {'object_name': 'FOIAFile'},
            'ffile': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'foia': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'files'", 'to': "orm['foia.FOIARequest']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'foia.foiaimage': {
            'Meta': {'unique_together': "(('foia', 'page'),)", 'object_name': 'FOIAImage'},
            'foia': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'images'", 'to': "orm['foia.FOIARequest']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'page': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        'foia.foiarequest': {
            'Meta': {'object_name': 'FOIARequest'},
            'agency': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'agency_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['foia.AgencyType']"}),
            'date_done': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'date_due': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'date_submitted': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'embargo': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jurisdiction': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'jurisdiction_new': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['foia.Jurisdiction']"}),
            'request': ('django.db.models.fields.TextField', [], {}),
            'response': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '70', 'db_index': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '70'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'foia.jurisdiction': {
            'Meta': {'object_name': 'Jurisdiction'},
            'abbrev': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['foia.Jurisdiction']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '55', 'db_index': 'True'})
        }
    }
    
    complete_apps = ['foia']
