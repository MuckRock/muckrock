"""This module will use the Django shell to generate some basic database entries"""
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=line-too-long

from datetime import datetime

from django.contrib.auth.models import User

from muckrock.accounts.models import Profile
from muckrock.agency.models import Agency
from muckrock.jurisdiction.models import Jurisdiction

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
# Fifth, create some communications
# Sixth, create some questions
# Seventh, create some news articles
