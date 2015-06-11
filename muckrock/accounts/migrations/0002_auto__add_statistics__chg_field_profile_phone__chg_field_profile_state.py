# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding model 'Statistics'
        db.create_table('accounts_statistics', (
            ('total_fees', self.gf('django.db.models.fields.IntegerField')()),
            ('total_pages', self.gf('django.db.models.fields.IntegerField')()),
            ('total_requests', self.gf('django.db.models.fields.IntegerField')()),
            ('total_requests_success', self.gf('django.db.models.fields.IntegerField')()),
            ('total_users', self.gf('django.db.models.fields.IntegerField')()),
            ('total_requests_denied', self.gf('django.db.models.fields.IntegerField')()),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('total_agencies', self.gf('django.db.models.fields.IntegerField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('accounts', ['Statistics'])

        # Adding M2M table for field users_today on 'Statistics'
        db.create_table('accounts_statistics_users_today', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('statistics', models.ForeignKey(orm['accounts.statistics'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('accounts_statistics_users_today', ['statistics_id', 'user_id'])

        # Changing field 'Profile.phone'
        db.alter_column('accounts_profile', 'phone', self.gf('localflavor.us.models.PhoneNumberField')(max_length=20, blank=True))

        # Changing field 'Profile.state'
        db.alter_column('accounts_profile', 'state', self.gf('localflavor.us.models.USStateField')(max_length=2, blank=True))


    def backwards(self, orm):

        # Deleting model 'Statistics'
        db.delete_table('accounts_statistics')

        # Removing M2M table for field users_today on 'Statistics'
        db.delete_table('accounts_statistics_users_today')

        # Changing field 'Profile.phone'
        db.alter_column('accounts_profile', 'phone', self.gf('localflavor.us.models.PhoneNumberField')(blank=True))

        # Changing field 'Profile.state'
        db.alter_column('accounts_profile', 'state', self.gf('localflavor.us.models.USStateField')(blank=True))


    models = {
        'accounts.profile': {
            'Meta': {'object_name': 'Profile'},
            'address1': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'address2': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '60', 'blank': 'True'}),
            'date_update': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'monthly_requests': ('django.db.models.fields.IntegerField', [], {'default': '5'}),
            'phone': ('localflavor.us.models.PhoneNumberField', [], {'max_length': '20', 'blank': 'True'}),
            'state': ('localflavor.us.models.USStateField', [], {'default': "'MA'", 'max_length': '2', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'}),
            'zip_code': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'accounts.statistics': {
            'Meta': {'object_name': 'Statistics'},
            'date': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'total_agencies': ('django.db.models.fields.IntegerField', [], {}),
            'total_fees': ('django.db.models.fields.IntegerField', [], {}),
            'total_pages': ('django.db.models.fields.IntegerField', [], {}),
            'total_requests': ('django.db.models.fields.IntegerField', [], {}),
            'total_requests_denied': ('django.db.models.fields.IntegerField', [], {}),
            'total_requests_success': ('django.db.models.fields.IntegerField', [], {}),
            'total_users': ('django.db.models.fields.IntegerField', [], {}),
            'users_today': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'symmetrical': 'False'})
        },
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
        }
    }

    complete_apps = ['accounts']
