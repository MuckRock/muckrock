# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Profile.email_confirmed'
        db.add_column(u'accounts_profile', 'email_confirmed',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Profile.confirmation_key'
        db.add_column(u'accounts_profile', 'confirmation_key',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=24, blank=True),
                      keep_default=False)

        # Adding field 'Profile.key_expire_date'
        db.add_column(u'accounts_profile', 'key_expire_date',
                      self.gf('django.db.models.fields.DateField')(null=True, blank=True),
                      keep_default=False)

    def backwards(self, orm):
        # Deleting field 'Profile.email_confirmed'
        db.delete_column(u'accounts_profile', 'email_confirmed')

        # Deleting field 'Profile.confirmation_key'
        db.delete_column(u'accounts_profile', 'confirmation_key')

        # Deleting field 'Profile.key_expire_date'
        db.delete_column(u'accounts_profile', 'key_expire_date')

        # Deleting field 'Profile.avatar'
        db.delete_column(u'accounts_profile', 'avatar')


    models = {
        u'accounts.profile': {
            'Meta': {'object_name': 'Profile'},
            'acct_type': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'address1': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'address2': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'avatar': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '60', 'blank': 'True'}),
            'confirmation_key': ('django.db.models.fields.CharField', [], {'max_length': '24', 'blank': 'True'}),
            'date_update': ('django.db.models.fields.DateField', [], {}),
            'email_confirmed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'email_pref': ('django.db.models.fields.CharField', [], {'default': "'daily'", 'max_length': '10'}),
            'follow_questions': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'follows_foia': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'followed_by'", 'blank': 'True', 'to': u"orm['foia.FOIARequest']"}),
            'follows_question': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'followed_by'", 'blank': 'True', 'to': u"orm['qanda.Question']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key_expire_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'linkedin': ('django.db.models.fields.URLField', [], {'max_length': '255', 'blank': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['jurisdiction.Jurisdiction']", 'null': 'True', 'blank': 'True'}),
            'monthly_requests': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'notifications': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'notify'", 'blank': 'True', 'to': u"orm['foia.FOIARequest']"}),
            'num_requests': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'users'", 'null': 'True', 'to': u"orm['organization.Organization']"}),
            'pgp_public_key': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'phone': ('django.contrib.localflavor.us.models.PhoneNumberField', [], {'max_length': '20', 'blank': 'True'}),
            'profile': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'public_email': ('django.db.models.fields.EmailField', [], {'max_length': '255', 'blank': 'True'}),
            'state': ('django.contrib.localflavor.us.models.USStateField', [], {'max_length': '2', 'blank': 'True'}),
            'stripe_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'twitter': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'use_autologin': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'unique': 'True'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '255', 'blank': 'True'}),
            'zip_code': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'})
        },
        u'accounts.statistics': {
            'Meta': {'ordering': "['-date']", 'object_name': 'Statistics'},
            'daily_articles': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'daily_requests_beta': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'daily_requests_community': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'daily_requests_pro': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'orphaned_communications': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'pro_user_names': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'pro_users': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'stale_agencies': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'total_agencies': ('django.db.models.fields.IntegerField', [], {}),
            'total_fees': ('django.db.models.fields.IntegerField', [], {}),
            'total_page_views': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'total_pages': ('django.db.models.fields.IntegerField', [], {}),
            'total_requests': ('django.db.models.fields.IntegerField', [], {}),
            'total_requests_abandoned': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'total_requests_awaiting_ack': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
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
            'unapproved_agencies': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'users_today': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.User']", 'symmetrical': 'False'})
        },
        u'agency.agency': {
            'Meta': {'object_name': 'Agency'},
            'address': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'appeal_agency': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['agency.Agency']", 'null': 'True', 'blank': 'True'}),
            'approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'can_email_appeals': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'contact_first_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'contact_last_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'contact_salutation': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'contact_title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'exempt': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'expires': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'fax': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'foia_guide': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'foia_logs': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'image_attr_line': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'jurisdiction': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'agencies'", 'to': u"orm['jurisdiction.Jurisdiction']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'other_emails': ('muckrock.fields.EmailsListField', [], {'max_length': '255', 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'public_notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255'}),
            'stale': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'twitter': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'twitter_handles': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'types': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['agency.AgencyType']", 'symmetrical': 'False', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'website': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'agency.agencytype': {
            'Meta': {'ordering': "['name']", 'object_name': 'AgencyType'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '60'})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'business_days.holiday': {
            'Meta': {'object_name': 'Holiday'},
            'day': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'month': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'num': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'weekday': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'foia.foiarequest': {
            'Meta': {'ordering': "['title']", 'object_name': 'FOIARequest'},
            'agency': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['agency.Agency']", 'null': 'True', 'blank': 'True'}),
            'block_incoming': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'date_done': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'date_due': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'date_embargo': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'date_followup': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'date_submitted': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'days_until_due': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'disable_autofollowups': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'edit_collaborators': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'edit_access'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'embargo': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'featured': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jurisdiction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['jurisdiction.Jurisdiction']"}),
            'mail_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'other_emails': ('muckrock.fields.EmailsListField', [], {'max_length': '255', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['foia.FOIARequest']", 'null': 'True', 'blank': 'True'}),
            'price': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '8', 'decimal_places': '2'}),
            'read_collaborators': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'read_access'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['auth.User']"}),
            'requested_docs': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'sidebar_html': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'times_viewed': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'tracker': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'tracking_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'updated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'jurisdiction.jurisdiction': {
            'Meta': {'ordering': "['name']", 'unique_together': "(('slug', 'parent'),)", 'object_name': 'Jurisdiction'},
            'abbrev': ('django.db.models.fields.CharField', [], {'max_length': '5', 'blank': 'True'}),
            'days': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '55', 'blank': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'holidays': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['business_days.Holiday']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'image_attr_line': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'intro': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'level': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'observe_sat': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': u"orm['jurisdiction.Jurisdiction']"}),
            'public_notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '55'}),
            'use_business_days': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'waiver': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        u'organization.organization': {
            'Meta': {'object_name': 'Organization'},
            'date_update': ('django.db.models.fields.DateField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'num_requests': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '255'}),
            'stripe_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'qanda.question': {
            'Meta': {'ordering': "['-date']", 'object_name': 'Question'},
            'answer_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'foia': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['foia.FOIARequest']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.TextField', [], {}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'tags.tag': {
            'Meta': {'ordering': "['name']", 'object_name': 'Tag', '_ormbases': [u'taggit.Tag']},
            u'tag_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['taggit.Tag']", 'unique': 'True', 'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        u'tags.taggeditembase': {
            'Meta': {'object_name': 'TaggedItemBase'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'tags_taggeditembase_tagged_items'", 'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'tags_taggeditembase_items'", 'to': u"orm['tags.Tag']"})
        }
    }

    complete_apps = ['accounts']