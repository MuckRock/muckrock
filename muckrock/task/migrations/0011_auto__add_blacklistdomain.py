# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'BlacklistDomain'
        db.create_table(u'task_blacklistdomain', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('domain', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal(u'task', ['BlacklistDomain'])


    def backwards(self, orm):
        # Deleting model 'BlacklistDomain'
        db.delete_table(u'task_blacklistdomain')


    models = {
        u'agency.agency': {
            'Meta': {'object_name': 'Agency'},
            'address': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'aliases': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
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
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': u"orm['agency.Agency']"}),
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
        u'crowdfund.crowdfundrequest': {
            'Meta': {'object_name': 'CrowdfundRequest'},
            'date_due': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'foia': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'crowdfund'", 'unique': 'True', 'to': "orm['foia.FOIARequest']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "'Crowdfund this request'", 'max_length': '255'}),
            'payment_received': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '8', 'decimal_places': '2'}),
            'payment_required': ('django.db.models.fields.DecimalField', [], {'default': "'0.00'", 'max_digits': '8', 'decimal_places': '2'})
        },
        'foia.foiacommunication': {
            'Meta': {'ordering': "['date']", 'object_name': 'FOIACommunication'},
            'communication': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'delivered': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'foia': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'communications'", 'null': 'True', 'to': "orm['foia.FOIARequest']"}),
            'from_who': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'full_html': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'likely_foia': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'likely_communications'", 'null': 'True', 'to': "orm['foia.FOIARequest']"}),
            'opened': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'priv_from_who': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'priv_to_who': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'response': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'to_who': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'foia.foiamultirequest': {
            'Meta': {'ordering': "['title']", 'object_name': 'FOIAMultiRequest'},
            'agencies': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'agencies'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['agency.Agency']"}),
            'embargo': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'requested_docs': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        'foia.foiarequest': {
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
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['foia.FOIARequest']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'permanent_embargo': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
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
            'law_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'level': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'observe_sat': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': u"orm['jurisdiction.Jurisdiction']"}),
            'public_notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '55'}),
            'use_business_days': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'waiver': ('django.db.models.fields.TextField', [], {'blank': 'True'})
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
        },
        u'task.blacklistdomain': {
            'Meta': {'object_name': 'BlacklistDomain'},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'task.crowdfundtask': {
            'Meta': {'ordering': "['date_created']", 'object_name': 'CrowdfundTask', '_ormbases': [u'task.Task']},
            'crowdfund': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['crowdfund.CrowdfundRequest']"}),
            u'task_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['task.Task']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'task.failedfaxtask': {
            'Meta': {'ordering': "['date_created']", 'object_name': 'FailedFaxTask', '_ormbases': [u'task.Task']},
            'communication': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['foia.FOIACommunication']"}),
            u'task_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['task.Task']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'task.flaggedtask': {
            'Meta': {'ordering': "['date_created']", 'object_name': 'FlaggedTask', '_ormbases': [u'task.Task']},
            'agency': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['agency.Agency']", 'null': 'True', 'blank': 'True'}),
            'foia': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['foia.FOIARequest']", 'null': 'True', 'blank': 'True'}),
            'jurisdiction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['jurisdiction.Jurisdiction']", 'null': 'True', 'blank': 'True'}),
            u'task_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['task.Task']", 'unique': 'True', 'primary_key': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'task.generictask': {
            'Meta': {'ordering': "['date_created']", 'object_name': 'GenericTask', '_ormbases': [u'task.Task']},
            'body': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'task_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['task.Task']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'task.multirequesttask': {
            'Meta': {'ordering': "['date_created']", 'object_name': 'MultiRequestTask', '_ormbases': [u'task.Task']},
            'multirequest': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['foia.FOIAMultiRequest']"}),
            u'task_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['task.Task']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'task.newagencytask': {
            'Meta': {'ordering': "['date_created']", 'object_name': 'NewAgencyTask', '_ormbases': [u'task.Task']},
            'agency': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['agency.Agency']"}),
            u'task_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['task.Task']", 'unique': 'True', 'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        u'task.orphantask': {
            'Meta': {'ordering': "['date_created']", 'object_name': 'OrphanTask', '_ormbases': [u'task.Task']},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'communication': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['foia.FOIACommunication']"}),
            'reason': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            u'task_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['task.Task']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'task.paymenttask': {
            'Meta': {'ordering': "['date_created']", 'object_name': 'PaymentTask', '_ormbases': [u'task.Task']},
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '2'}),
            'foia': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['foia.FOIARequest']"}),
            u'task_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['task.Task']", 'unique': 'True', 'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'task.rejectedemailtask': {
            'Meta': {'ordering': "['date_created']", 'object_name': 'RejectedEmailTask', '_ormbases': [u'task.Task']},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'error': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'foia': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['foia.FOIARequest']", 'null': 'True', 'blank': 'True'}),
            u'task_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['task.Task']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'task.responsetask': {
            'Meta': {'ordering': "['date_created']", 'object_name': 'ResponseTask', '_ormbases': [u'task.Task']},
            'communication': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['foia.FOIACommunication']"}),
            u'task_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['task.Task']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'task.snailmailtask': {
            'Meta': {'ordering': "['date_created']", 'object_name': 'SnailMailTask', '_ormbases': [u'task.Task']},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'communication': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['foia.FOIACommunication']"}),
            u'task_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['task.Task']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'task.staleagencytask': {
            'Meta': {'ordering': "['date_created']", 'object_name': 'StaleAgencyTask', '_ormbases': [u'task.Task']},
            'agency': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['agency.Agency']"}),
            u'task_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['task.Task']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'task.statuschangetask': {
            'Meta': {'ordering': "['date_created']", 'object_name': 'StatusChangeTask', '_ormbases': [u'task.Task']},
            'foia': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['foia.FOIARequest']"}),
            'old_status': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'task_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['task.Task']", 'unique': 'True', 'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'task.task': {
            'Meta': {'ordering': "['date_created']", 'object_name': 'Task'},
            'assigned': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'assigned_tasks'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_done': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'resolved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'resolved_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'resolved_tasks'", 'null': 'True', 'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['task']