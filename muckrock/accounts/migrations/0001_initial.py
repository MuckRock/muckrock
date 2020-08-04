# -*- coding: utf-8 -*-

# Django
from django.conf import settings
from django.db import migrations, models

# Third Party
import easy_thumbnails.fields
import localflavor.us.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                (
                    'id',
                    models.AutoField(
                        verbose_name='ID',
                        serialize=False,
                        auto_created=True,
                        primary_key=True
                    )
                ),
                (
                    'address1',
                    models.CharField(
                        max_length=50, verbose_name='address', blank=True
                    )
                ),
                (
                    'address2',
                    models.CharField(
                        max_length=50,
                        verbose_name='address (line 2)',
                        blank=True
                    )
                ),
                ('city', models.CharField(max_length=60, blank=True)),
                (
                    'state',
                    localflavor.us.models.USStateField(
                        blank=True,
                        help_text=
                        'Your state will be made public on this site.If you do not want this information to be public, please leave blank.',
                        max_length=2,
                        choices=[
                            ('AL', 'Alabama'), ('AK', 'Alaska'),
                            ('AS', 'American Samoa'), ('AZ', 'Arizona'),
                            ('AR', 'Arkansas'), ('AA', 'Armed Forces Americas'),
                            ('AE', 'Armed Forces Europe'),
                            ('AP',
                             'Armed Forces Pacific'), ('CA', 'California'),
                            ('CO',
                             'Colorado'), ('CT',
                                           'Connecticut'), ('DE', 'Delaware'),
                            ('DC', 'District of Columbia'), ('FL', 'Florida'),
                            ('GA',
                             'Georgia'), ('GU',
                                          'Guam'), ('HI',
                                                    'Hawaii'), ('ID', 'Idaho'),
                            ('IL', 'Illinois'), ('IN',
                                                 'Indiana'), ('IA', 'Iowa'),
                            ('KS', 'Kansas'), ('KY',
                                               'Kentucky'), ('LA', 'Louisiana'),
                            ('ME',
                             'Maine'), ('MD',
                                        'Maryland'), ('MA', 'Massachusetts'),
                            ('MI',
                             'Michigan'), ('MN',
                                           'Minnesota'), ('MS', 'Mississippi'),
                            ('MO', 'Missouri'), ('MT',
                                                 'Montana'), ('NE', 'Nebraska'),
                            ('NV', 'Nevada'), ('NH', 'New Hampshire'),
                            ('NJ',
                             'New Jersey'), ('NM',
                                             'New Mexico'), ('NY', 'New York'),
                            ('NC', 'North Carolina'), ('ND', 'North Dakota'),
                            ('MP', 'Northern Mariana Islands'), ('OH', 'Ohio'),
                            ('OK',
                             'Oklahoma'), ('OR',
                                           'Oregon'), ('PA', 'Pennsylvania'),
                            ('PR', 'Puerto Rico'), ('RI', 'Rhode Island'),
                            ('SC', 'South Carolina'), ('SD', 'South Dakota'),
                            ('TN', 'Tennessee'), ('TX',
                                                  'Texas'), ('UT', 'Utah'),
                            ('VT', 'Vermont'), ('VI', 'Virgin Islands'),
                            ('VA', 'Virginia'), ('WA', 'Washington'),
                            ('WV',
                             'West Virginia'), ('WI',
                                                'Wisconsin'), ('WY', 'Wyoming')
                        ]
                    )
                ),
                ('zip_code', models.CharField(max_length=10, blank=True)),
                (
                    'phone',
                    models.CharField(
                        max_length=20, blank=True
                    )
                ),
                ('follow_questions', models.BooleanField(default=False)),
                (
                    'acct_type',
                    models.CharField(
                        max_length=10,
                        choices=[('admin', 'Admin'), ('beta', 'Beta'),
                                 ('community', 'Community'),
                                 ('pro', 'Professional'), ('proxy', 'Proxy')]
                    )
                ),
                ('email_confirmed', models.BooleanField(default=False)),
                (
                    'confirmation_key',
                    models.CharField(max_length=24, blank=True)
                ),
                ('profile', models.TextField(blank=True)),
                ('public_email', models.EmailField(max_length=255, blank=True)),
                ('pgp_public_key', models.TextField(blank=True)),
                (
                    'website',
                    models.URLField(
                        help_text='Begin with http://',
                        max_length=255,
                        blank=True
                    )
                ),
                ('twitter', models.CharField(max_length=255, blank=True)),
                (
                    'linkedin',
                    models.URLField(
                        help_text='Begin with http://',
                        max_length=255,
                        blank=True
                    )
                ),
                (
                    'avatar',
                    easy_thumbnails.fields.ThumbnailerImageField(
                        null=True, upload_to='account_images', blank=True
                    )
                ),
                (
                    'email_pref',
                    models.CharField(
                        default='daily',
                        help_text=
                        'Receive email updates to your requests instantly or in a daily or weekly digest',
                        max_length=10,
                        verbose_name='Email Preference',
                        choices=[('instant', 'Instant'), ('daily', 'Daily'),
                                 ('weekly', 'Weekly')]
                    )
                ),
                (
                    'use_autologin',
                    models.BooleanField(
                        default=True,
                        help_text=
                        'Links you receive in emails from us will contain a one time token to automatically log you in'
                    )
                ),
                ('num_requests', models.IntegerField(default=0)),
                ('monthly_requests', models.IntegerField(default=0)),
                ('date_update', models.DateField()),
                ('stripe_id', models.CharField(max_length=255, blank=True)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Statistics',
            fields=[
                (
                    'id',
                    models.AutoField(
                        verbose_name='ID',
                        serialize=False,
                        auto_created=True,
                        primary_key=True
                    )
                ),
                ('date', models.DateField()),
                ('total_requests', models.IntegerField()),
                ('total_requests_success', models.IntegerField()),
                ('total_requests_denied', models.IntegerField()),
                (
                    'total_requests_draft',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_requests_submitted',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_requests_awaiting_ack',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_requests_awaiting_response',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_requests_awaiting_appeal',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_requests_fix_required',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_requests_payment_required',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_requests_no_docs',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_requests_partial',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_requests_abandoned',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'orphaned_communications',
                    models.IntegerField(null=True, blank=True)
                ),
                ('total_agencies', models.IntegerField()),
                ('stale_agencies', models.IntegerField(null=True, blank=True)),
                (
                    'unapproved_agencies',
                    models.IntegerField(null=True, blank=True)
                ),
                ('total_pages', models.IntegerField()),
                ('total_users', models.IntegerField()),
                ('total_fees', models.IntegerField()),
                ('pro_users', models.IntegerField(null=True, blank=True)),
                ('pro_user_names', models.TextField(blank=True)),
                (
                    'total_page_views',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'daily_requests_pro',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'daily_requests_community',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'daily_requests_beta',
                    models.IntegerField(null=True, blank=True)
                ),
                ('daily_articles', models.IntegerField(null=True, blank=True)),
                ('total_tasks', models.IntegerField(null=True, blank=True)),
                (
                    'total_unresolved_tasks',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_generic_tasks',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_unresolved_generic_tasks',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_orphan_tasks',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_unresolved_orphan_tasks',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_snailmail_tasks',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_unresolved_snailmail_tasks',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_rejected_tasks',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_unresolved_rejected_tasks',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_staleagency_tasks',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_unresolved_staleagency_tasks',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_flagged_tasks',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_unresolved_flagged_tasks',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_newagency_tasks',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_unresolved_newagency_tasks',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_response_tasks',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_unresolved_response_tasks',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_faxfail_tasks',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_unresolved_faxfail_tasks',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_payment_tasks',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_unresolved_payment_tasks',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_crowdfundpayment_tasks',
                    models.IntegerField(null=True, blank=True)
                ),
                (
                    'total_unresolved_crowdfundpayment_tasks',
                    models.IntegerField(null=True, blank=True)
                ),
                ('public_notes', models.TextField(default='', blank=True)),
                ('admin_notes', models.TextField(default='', blank=True)),
                (
                    'users_today',
                    models.ManyToManyField(to=settings.AUTH_USER_MODEL)
                ),
            ],
            options={
                'ordering': ['-date'],
                'verbose_name_plural': 'statistics',
            },
            bases=(models.Model,),
        ),
    ]
