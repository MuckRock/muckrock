"""This module will use the Django shell to generate some basic database entries"""
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=line-too-long

from datetime import datetime

from django.contrib.auth.models import User

from muckrock.accounts.models import Profile
from muckrock.agency.models import Agency
from muckrock.foia.models import FOIARequest, FOIACommunication
from muckrock.jurisdiction.models import Jurisdiction
from muckrock.task.models import *

# First, create some accounts

user = User.objects.create(username='User1', password='password', first_name='User', last_name='One')

profile = Profile.objects.create(user=user, acct_type='community', date_update=datetime.now())

# Second, create some jurisdictions

federal = Jurisdiction.objects.create(name='United States of America', slug='united-states-of-america', level='f')

state = Jurisdiction.objects.create(name='New Jersey', slug='new-jersey', abbrev='NJ', level='s', parent=federal)

local = Jurisdiction.objects.create(name='Newark', slug='newark-nj', level='l', parent=state)

# Third, create some agencies

usa_fbi = Agency.objects.create(name='Federal Bureau of Investigation', slug='federal-bureau-investigation', jurisdiction=federal, approved=True)

nj_gov = Agency.objects.create(name='Governor\'s Office', slug='nj-governors-office', jurisdiction=state, approved=True)

newark_mayor = Agency.objects.create(name='Mayor\'s Office', slug='nj-mayors-office', jurisdiction=local, approved=True)

# Fourth, create some requests

foia1 = FOIARequest.objects.create(user=user, title='Test Request', slug='test-request', status='submitted', jurisdiction=federal, agency=usa_fbi, date_submitted=datetime.now())

foia2 = FOIARequest.objects.create(user=user, title='Test Request', slug='test-request', status='submitted', jurisdiction=state, agency=nj_gov, date_submitted=datetime.now())

foia3 = FOIARequest.objects.create(user=user, title='Test Request', slug='test-request', status='submitted', jurisdiction=local, agency=newark_mayor, date_submitted=datetime.now())

# Fifth, create some communications

comm11 = FOIACommunication.objects.create(foia=foia1, from_who='Person A', to_who='Person B', priv_from_who='Alice', priv_to_who='Bob', date=datetime.now(), response=False, communication='Lorem ipsum dolor su ament', delivered='email')

comm12 = FOIACommunication.objects.create(foia=foia1, from_who='Person B', to_who='Person A', priv_from_who='Bob', priv_to_who='Alice', date=datetime.now(), response=True, communication='Lorem ipsum dolor su ament', delivered='email')

comm21 = FOIACommunication.objects.create(foia=foia2, from_who='Person A', to_who='Person B', priv_from_who='Alice', priv_to_who='Bob', date=datetime.now(), response=False, communication='Lorem ipsum dolor su ament', delivered='email')

comm22 = FOIACommunication.objects.create(foia=foia2, from_who='Person B', to_who='Person A', priv_from_who='Bob', priv_to_who='Alice', date=datetime.now(), response=True, communication='Lorem ipsum dolor su ament', delivered='email')

comm31 = FOIACommunication.objects.create(foia=foia3, from_who='Person A', to_who='Person B', priv_from_who='Alice', priv_to_who='Bob', date=datetime.now(), response=False, communication='Lorem ipsum dolor su ament', delivered='email')

comm32 = FOIACommunication.objects.create(foia=foia3, from_who='Person B', to_who='Person A', priv_from_who='Bob', priv_to_who='Alice', date=datetime.now(), response=True, communication='Lorem ipsum dolor su ament', delivered='email')

# Sixth, create some tasks

orphan = OrphanTask.objects.create(reason='bs', communication=comm, address='100dollars@bigmoney.biz')

snail_mail = SnailMailTask.objects.create(category='a', communication=comm)

rejected_email = RejectedEmailTask.objects.create(category='b', foia=foia1, email='bigdog@bostondynamics.com', error='Undeliverable')

stale_agency = StaleAgencyTask.objects.create(agency=nj_gov)

flagged_foia = FlaggedTask.objects.create(user=user, text='I hate this.', foia=foia1)

flagged_agency = FlaggedTask.objects.create(user=user, text='I also hate this.', agency=nj_gov)

flagged_jurisdiction = FlaggedTask.objects.create(user=user, text='I hate this the most tho', jurisdiction=local)

new_agency = NewAgencyTask.objects.create(user=user, agency=newark_mayor)

response = ResponseTask.objects.create(communication=comm32)

# Seventh, create some questions
# Eighth, create some news articles
