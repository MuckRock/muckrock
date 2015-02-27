# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding field 'Statistics.total_requests_draft'
        db.add_column('accounts_statistics', 'total_requests_draft', self.gf('django.db.models.fields.IntegerField')(null=True), keep_default=False)

        # Adding field 'Statistics.daily_requests_pro'
        db.add_column('accounts_statistics', 'daily_requests_pro', self.gf('django.db.models.fields.IntegerField')(null=True), keep_default=False)

        # Adding field 'Statistics.total_requests_partial'
        db.add_column('accounts_statistics', 'total_requests_partial', self.gf('django.db.models.fields.IntegerField')(null=True), keep_default=False)

        # Adding field 'Statistics.daily_articles'
        db.add_column('accounts_statistics', 'daily_articles', self.gf('django.db.models.fields.IntegerField')(null=True), keep_default=False)

        # Adding field 'Statistics.daily_requests_community'
        db.add_column('accounts_statistics', 'daily_requests_community', self.gf('django.db.models.fields.IntegerField')(null=True), keep_default=False)

        # Adding field 'Statistics.total_requests_abandoned'
        db.add_column('accounts_statistics', 'total_requests_abandoned', self.gf('django.db.models.fields.IntegerField')(null=True), keep_default=False)

        # Adding field 'Statistics.total_requests_payment_required'
        db.add_column('accounts_statistics', 'total_requests_payment_required', self.gf('django.db.models.fields.IntegerField')(null=True), keep_default=False)

        # Adding field 'Statistics.total_requests_awaiting_appeal'
        db.add_column('accounts_statistics', 'total_requests_awaiting_appeal', self.gf('django.db.models.fields.IntegerField')(null=True), keep_default=False)

        # Adding field 'Statistics.pro_user_names'
        db.add_column('accounts_statistics', 'pro_user_names', self.gf('django.db.models.fields.TextField')(default='', blank=True), keep_default=False)

        # Adding field 'Statistics.total_requests_no_docs'
        db.add_column('accounts_statistics', 'total_requests_no_docs', self.gf('django.db.models.fields.IntegerField')(null=True), keep_default=False)

        # Adding field 'Statistics.pro_users'
        db.add_column('accounts_statistics', 'pro_users', self.gf('django.db.models.fields.IntegerField')(null=True), keep_default=False)

        # Adding field 'Statistics.total_requests_fix_required'
        db.add_column('accounts_statistics', 'total_requests_fix_required', self.gf('django.db.models.fields.IntegerField')(null=True), keep_default=False)

        # Adding field 'Statistics.daily_requests_beta'
        db.add_column('accounts_statistics', 'daily_requests_beta', self.gf('django.db.models.fields.IntegerField')(null=True), keep_default=False)

        # Adding field 'Statistics.total_requests_awaiting_response'
        db.add_column('accounts_statistics', 'total_requests_awaiting_response', self.gf('django.db.models.fields.IntegerField')(null=True), keep_default=False)

        # Adding field 'Statistics.total_requests_submitted'
        db.add_column('accounts_statistics', 'total_requests_submitted', self.gf('django.db.models.fields.IntegerField')(null=True), keep_default=False)

        # Adding field 'Statistics.total_page_views'
        db.add_column('accounts_statistics', 'total_page_views', self.gf('django.db.models.fields.IntegerField')(null=True), keep_default=False)


    def backwards(self, orm):

        # Deleting field 'Statistics.total_requests_draft'
        db.delete_column('accounts_statistics', 'total_requests_draft')

        # Deleting field 'Statistics.daily_requests_pro'
        db.delete_column('accounts_statistics', 'daily_requests_pro')

        # Deleting field 'Statistics.total_requests_partial'
        db.delete_column('accounts_statistics', 'total_requests_partial')

        # Deleting field 'Statistics.daily_articles'
        db.delete_column('accounts_statistics', 'daily_articles')

        # Deleting field 'Statistics.daily_requests_community'
        db.delete_column('accounts_statistics', 'daily_requests_community')

        # Deleting field 'Statistics.total_requests_abandoned'
        db.delete_column('accounts_statistics', 'total_requests_abandoned')

        # Deleting field 'Statistics.total_requests_payment_required'
        db.delete_column('accounts_statistics', 'total_requests_payment_required')

        # Deleting field 'Statistics.total_requests_awaiting_appeal'
        db.delete_column('accounts_statistics', 'total_requests_awaiting_appeal')

        # Deleting field 'Statistics.pro_user_names'
        db.delete_column('accounts_statistics', 'pro_user_names')

        # Deleting field 'Statistics.total_requests_no_docs'
        db.delete_column('accounts_statistics', 'total_requests_no_docs')

        # Deleting field 'Statistics.pro_users'
        db.delete_column('accounts_statistics', 'pro_users')

        # Deleting field 'Statistics.total_requests_fix_required'
        db.delete_column('accounts_statistics', 'total_requests_fix_required')

        # Deleting field 'Statistics.daily_requests_beta'
        db.delete_column('accounts_statistics', 'daily_requests_beta')

        # Deleting field 'Statistics.total_requests_awaiting_response'
        db.delete_column('accounts_statistics', 'total_requests_awaiting_response')

        # Deleting field 'Statistics.total_requests_submitted'
        db.delete_column('accounts_statistics', 'total_requests_submitted')

        # Deleting field 'Statistics.total_page_views'
        db.delete_column('accounts_statistics', 'total_page_views')


    models = {
        'accounts.profile': {
            'Meta': {'object_name': 'Profile'},
            'acct_type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'address1': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'address2': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '60', 'blank': 'True'}),
            'date_update': ('django.db.models.fields.DateField', [], {}),
            'follows': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'followed_by'", 'blank': 'True', 'to': "orm['foia.FOIARequest']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'monthly_requests': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'num_requests': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'phone': ('django.contrib.localflavor.us.models.PhoneNumberField', [], {'max_length': '20', 'blank': 'True'}),
            'state': ('django.contrib.localflavor.us.models.USStateField', [], {'default': "'MA'", 'max_length': '2', 'blank': 'True'}),
            'stripe_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'}),
            'zip_code': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        'accounts.statistics': {
            'Meta': {'object_name': 'Statistics'},
            'daily_articles': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'daily_requests_beta': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'daily_requests_community': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'daily_requests_pro': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pro_user_names': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'pro_users': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'total_agencies': ('django.db.models.fields.IntegerField', [], {}),
            'total_fees': ('django.db.models.fields.IntegerField', [], {}),
            'total_page_views': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'total_pages': ('django.db.models.fields.IntegerField', [], {}),
            'total_requests': ('django.db.models.fields.IntegerField', [], {}),
            'total_requests_abandoned': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'total_requests_awaiting_appeal': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'total_requests_awaiting_response': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'total_requests_denied': ('django.db.models.fields.IntegerField', [], {}),
            'total_requests_draft': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'total_requests_fix_required': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'total_requests_no_docs': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'total_requests_partial': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'total_requests_payment_required': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'total_requests_submitted': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'total_requests_success': ('django.db.models.fields.IntegerField', [], {}),
            'total_users': ('django.db.models.fields.IntegerField', [], {}),
            'users_today': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'symmetrical': 'False'})
        },
        'agency.agency': {
            'Meta': {'object_name': 'Agency'},
            'address': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'appeal_agency': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['agency.Agency']", 'null': 'True', 'blank': 'True'}),
            'approved': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'can_email_appeals': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'contact_first_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'contact_last_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'contact_salutation': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'contact_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'expires': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'fax': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'image_attr_line': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'jurisdiction': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'agencies'", 'to': "orm['jurisdiction.Jurisdiction']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'other_emails': ('muckrock.fields.EmailsListField', [], {'max_length': '255', 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'public_notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255', 'db_index': 'True'}),
            'types': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['agency.AgencyType']", 'symmetrical': 'False', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'agency.agencytype': {
            'Meta': {'object_name': 'AgencyType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'})
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
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 3, 12, 22, 35, 17, 447814)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 3, 12, 22, 35, 17, 447722)'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'business_days.holiday': {
            'Meta': {'object_name': 'Holiday'},
            'day': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'month': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'num': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'weekday': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'foia.foiarequest': {
            'Meta': {'object_name': 'FOIARequest'},
            'agency': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['agency.Agency']", 'null': 'True', 'blank': 'True'}),
            'date_done': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'date_due': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'date_embargo': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'date_followup': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'date_submitted': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'days_until_due': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'embargo': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'featured': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jurisdiction': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['jurisdiction.Jurisdiction']"}),
            'mail_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'other_emails': ('muckrock.fields.EmailsListField', [], {'max_length': '255', 'blank': 'True'}),
            'price': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '8', 'decimal_places': '2'}),
            'sidebar_html': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255', 'db_index': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'times_viewed': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'tracker': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'tracking_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'updated': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'jurisdiction.jurisdiction': {
            'Meta': {'unique_together': "(('slug', 'parent'),)", 'object_name': 'Jurisdiction'},
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
        },
        'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'})
        },
        'tags.tag': {
            'Meta': {'object_name': 'Tag', '_ormbases': ['taggit.Tag']},
            'tag_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['taggit.Tag']", 'unique': 'True', 'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'tags.taggeditembase': {
            'Meta': {'object_name': 'TaggedItemBase'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tags_taggeditembase_tagged_items'", 'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tags_taggeditembase_items'", 'to': "orm['tags.Tag']"})
        }
    }

    complete_apps = ['accounts']
