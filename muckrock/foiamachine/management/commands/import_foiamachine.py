# pylint: skip-file

# Django
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

# Standard Library
import csv
import os
from datetime import date, datetime

# Third Party
from boto.s3.connection import S3Connection
from dateutil import parser
from fuzzywuzzy import fuzz, process
from localflavor.us.forms import USPhoneNumberField
from localflavor.us.us_states import STATES_NORMALIZED
from smart_open import smart_open

# MuckRock
from muckrock.accounts.models import Profile
from muckrock.accounts.utils import unique_username
from muckrock.agency.models import Agency
from muckrock.foiamachine.models import (
    FoiaMachineCommunication,
    FoiaMachineFile,
    FoiaMachineRequest,
)
from muckrock.jurisdiction.models import Jurisdiction

CSV_OPTS = {
    'doublequote': False,
    'escapechar': '\\',
    'lineterminator': '\n',
    'strict': True,
}


class Command(BaseCommand):
    """
    Command to run a one time import of FOIA Machine datat from CSV files
    exported to S3
    """

    def handle(self, *args, **kwargs):
        """Do all the imports"""
        # do this in a transaction
        # if their are any errors, make no changes to the database
        conn = S3Connection(
            settings.AWS_ACCESS_KEY_ID,
            settings.AWS_SECRET_ACCESS_KEY,
        )
        self.bucket = conn.get_bucket('muckrock')
        self.stdout.write('Beginning import...')
        with transaction.atomic():
            self.import_users()
            self.import_requests()
            communication_map = self.import_communications()
            self.import_files(communication_map)
        self.stdout.write('Import succesful!')

    def import_users(self):
        """Import all of the users"""
        count = 0
        self.stdout.write('Importing users...')
        key = self.bucket.get_key('foiamachine/data/fm_users.csv')
        user_log_key = self.bucket.new_key('foiamachine/data/user_log.csv')
        with smart_open(key) as users_file, smart_open(
            user_log_key, 'wb'
        ) as user_log_file:
            users = csv.reader(users_file, **CSV_OPTS)
            user_log = csv.writer(user_log_file, **CSV_OPTS)
            user_log.writerow([
                'muckrock username',
                'foia machine username',
                'email',
                'first_name',
                'last_name',
                'new account',
                'new username',
            ])
            next(users)  # drop the headers
            for (
                username, first_name, last_name, email, password, is_active,
                last_login, date_joined, mailing_address, mailing_city,
                mailing_state, mailing_zip, phone, is_verified
            ) in users:
                # only create users who do not already have an account
                # associated with their email
                new_username = unique_username(username)
                defaults = {
                    'username': new_username,
                    'first_name': first_name,
                    'last_name': last_name,
                    'password': password,
                    'is_staff': False,
                    'is_active': is_active == '1',
                    'is_superuser': False,
                    'last_login': parser.parse(last_login),
                    'date_joined': parser.parse(date_joined),
                }
                if email:
                    user, created = User.objects.get_or_create(
                        email=email,
                        defaults=defaults,
                    )
                else:
                    continue
                user_log.writerow([
                    user.username,
                    username,
                    email,
                    first_name,
                    last_name,
                    created,
                    user.username != username,
                ])
                # if we created a new user, create their corresponding profile
                if created:
                    count += 1
                    if mailing_state.strip():
                        mailing_state = mailing_state.strip().lower().replace(
                            '.', ''
                        )
                        try:
                            state = STATES_NORMALIZED[mailing_state]
                        except KeyError:
                            if '-' in mailing_state:
                                try:
                                    state = STATES_NORMALIZED[
                                        mailing_state.split('-')[0].strip()
                                    ]
                                except KeyError:
                                    # print 'Bad state:', mailing_state
                                    pass
                            elif ' ' in mailing_state:
                                try:
                                    state = STATES_NORMALIZED[
                                        mailing_state.split(' ')[0].strip()
                                    ]
                                except KeyError:
                                    # print 'Bad state:', mailing_state
                                    pass
                            else:
                                # print 'Bad state:', mailing_state
                                pass
                    else:
                        state = ''
                    if phone:
                        try:
                            phone = USPhoneNumberField().clean(phone)
                        except ValidationError:
                            # print 'Bad phone:', phone
                            pass
                    else:
                        phone = ''
                    if len(mailing_zip) > 10:
                        # print 'Bad zip:', mailing_zip
                        mailing_zip = ''
                    if len(mailing_address) > 50:
                        # print 'Bad address:', mailing_address
                        mailing_address = ''
                    Profile.objects.create(
                        user=user,
                        address1=mailing_address,
                        city=mailing_city,
                        state=state,
                        zip_code=mailing_zip,
                        phone=phone,
                        email_confirmed=is_verified,
                        acct_type='basic',
                        num_requests=5,
                        source='foia machine',
                        date_update=date.today(),
                    )
        print 'Imported %s new users' % count

    def import_requests(self):
        """Import all of the requests"""
        self.stdout.write('Importing requests...')
        key = self.bucket.get_key('foiamachine/data/fm_requests.csv')
        count = 0
        with smart_open(key) as requests_file:
            requests = csv.reader(requests_file, **CSV_OPTS)
            next(requests)  # drop the headers
            status_map = {
                'X': 'abandoned',
                'I': 'started',
                'U': 'submitted',
                'S': 'ack',
                'R': 'processed',
                'P': 'partial',
                'F': 'done',
                'D': 'rejected',
            }
            jurisdictions = {
                j.name: j
                for j in Jurisdiction.objects.filter(level__in=('f', 's'))
            }
            agencies = {
                j.name: Agency.objects.filter(
                    Q(jurisdiction=j) | Q(jurisdiction__parent=j),
                    status='approved'
                )
                for j in jurisdictions.itervalues()
            }
            agencies['United States of America'] = Agency.objects.filter(
                jurisdiction=jurisdictions['United States of America'],
                status='approved'
            )
            seen = set()
            for (
                user_email, title, status, jurisdiction_name, agency_name, text,
                slug, date_added
            ) in requests:
                if status == 'X':
                    continue
                if jurisdiction_name == 'N':
                    jurisdiction = None
                else:
                    jurisdiction = jurisdictions[jurisdiction_name]
                if agency_name == 'N':
                    agency = None
                else:
                    agency_score = process.extractOne(
                        agency_name,
                        agencies[jurisdiction_name],
                        scorer=fuzz.token_set_ratio,
                    )
                    if agency_score:
                        agency, score = agency_score
                    else:
                        agency, score = None, 0
                    if score < 100 and agency_name not in seen:
                        # print 'J: %s - score: %s\n\t%s\n\t%s' % (jurisdiction, score, agency_name, agency)
                        seen.add(agency_name)
                    if score < 89:
                        agency = None
                count += 1
                req = FoiaMachineRequest(
                    user=User.objects.get(email=user_email),
                    title=title,
                    slug=slug,
                    date_created=parser.parse(date_added),
                    status=status_map[status],
                    request_language=text,
                    jurisdiction=jurisdiction,
                    agency=agency,
                )
                req.save(autoslug=False)
        print 'Imported %s requests' % count

    def import_communications(self):
        """Import all communications"""
        self.stdout.write('Importing communications...')
        communication_map = {}
        count = 0
        key = self.bucket.get_key('foiamachine/data/fm_communications.csv')
        seen = set()
        with smart_open(key) as comms_file:
            comms = csv.reader(comms_file, **CSV_OPTS)
            next(comms)  # drop the headers
            for (
                email_from, email_to, body, subject, dated, request_slug,
                direction, comm_id
            ) in comms:
                try:
                    request = FoiaMachineRequest.objects.get(slug=request_slug)
                except FoiaMachineRequest.DoesNotExist:
                    if request_slug not in seen:
                        print 'Request not found', request_slug
                        seen.add(request_slug)
                    continue
                try:
                    date = parser.parse(dated)
                except ValueError:  # null dated
                    date = datetime.now()
                if len(subject) > 255:
                    print 'Subject too big:', subject
                comm = FoiaMachineCommunication.objects.create(
                    request=request,
                    sender=email_from,
                    receiver=email_to,
                    subject=subject[:255],
                    message=body,
                    date=date,
                    received=(direction == 'R'),
                )
                count += 1
                # use the id to track the pk so we can attach the files to
                # the correct communication
                communication_map[comm_id] = comm
        print 'Imported %s communications' % count
        return communication_map

    def import_files(self, communication_map):
        """Import FOIA Files"""
        self.stdout.write('Importing files...')
        count = 0
        key = self.bucket.get_key('foiamachine/data/fm_files.csv')
        with smart_open(key) as files_file:
            files = csv.reader(files_file, **CSV_OPTS)
            next(files)
            for file_, created, comm_id in files:
                if comm_id not in communication_map:
                    continue
                file_name = os.path.splitext(os.path.basename(file_))[0]
                FoiaMachineFile.objects.create(
                    communication=communication_map[comm_id],
                    file='foiamachine_files/' + file_,
                    date_added=parser.parse(created),
                    name=file_name,
                )
                count += 1
        print 'Imported %s files' % count
