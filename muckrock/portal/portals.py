# -*- coding: utf-8 -*-
"""Logic for the different portal types"""

from django.conf import settings

import requests
import string

from muckrock.task.models import PortalTask
from muckrock.utils import generate_key


class ManualPortal(object):
    """A fall-back type to manually handle portals we cannot automate yet"""

    @classmethod
    def send_msg(cls, comm, **kwargs):
        """Send a message via the portal"""
        category, _ = comm.foia.process_manual_send(**kwargs)
        PortalTask.objects.create(
                category=category,
                communication=comm,
                )

    @classmethod
    def receive_msg(cls, comm):
        """Receive a message from the portal"""
        PortalTask.objects.create(
                category='i',
                communication=comm,
                )

    @classmethod
    def get_new_password(cls):
        """Generate a random password to use with this portal"""
        chars = string.ascii_letters + string.digits + string.punctuation
        return generate_key(12, chars=chars)


class NextRequest(ManualPortal):
    """NextRequest Portal integration"""
    # pylint: disable=all

    def send_msg(self, comm, **kwargs):
        # spaces may need to be plus signs?

        foia = comm.foia
        user = foia.user
        email = '%s@%s' % (foia.get_mail_id(), settings.MAILGUN_SERVER_NAME)
        password = generate_key(12)

        session = requests.Session()
        session.get(self.url + '/requests/new')

        # get from /requests/new to get csrf token
        # get csrf token from header: <meta name="csrf-token" content="{token}">
        # post to /requests
        data = {
                'request[subtitle]': foia.title, # ???
                'request[request_text]': foia.communications.first().requested_docs,
                'requester[email]': email,
                'requester[name]': user.get_full_name(),
                'requester[phone_number]': '(617) 299-1873',
                'requester[address]': '411A Highland Ave',
                'requester[city]': 'Somerville',
                'requester[state]': 'MA',
                'requester[zipcode]': '02144',
                'requester[company]': '',
                'utf8': '✓',
                'authenticity_token': '',
                'commit': 'Make Request',
                }
        # read response for new csrf token
        # post to /passwords
        data = {
                'user[email]': email,
                'user[password]': password,
                'user[password_confirmation]': password,
                'utf8': '✓',
                'authenticity_token': '',
                'commit': 'Save',
                }

        # confirm email address
        # do not post administrative emails

    def receive_email(self):
        # login to site and retrieve
        #  - text reply
        #  - download files
        #  - fetch status
        pass
