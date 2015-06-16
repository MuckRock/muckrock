"""
Projects are a way to quickly introduce our audience to the
topics and issues we cover and then provide them avenues for
deeper, sustained involvement with our work on those topics.
"""

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from muckrock.project.models import Project

import nose

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_

"""
* Projects must have a title.
* Projects should have a statement describing their purpose.
* Projects should have an image or illustration to accompany them.
* Projects should keep a list of users who are contributors.
* Projects should keep a list of relevant requests.
* Projects should keep a list of relevant articles.
* Projects should keep a list of relevant keywords/tags.
* Projects should be kept very flexible and nonprescritive.
* Projects should be able to be made private.
"""

class TestProject(TestCase):

    fixtures = ['test_users.json']

    def test_create_new_project(self):
        """
        Create a new project:
        * Projects must have a title.
        * Projects should have a statement describing their purpose.
        * Projects should have an image or illustration to accompany them.
        """
        minimum_project = Project(title='Private Prisons')
        minimum_project.save()
        ok_(minimum_project)
        test_image = SimpleUploadedFile(
            name='foo.gif',
            content=(b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,'
                    '\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00')
        )
        ideal_project = Project(
            title='Private Prisons',
            description=('The prison industry is growing at an alarming rate. '
                        'Even more alarming? The conditions inside prisions '
                        'are growing worse while their tax-dollar derived '
                        'profits are growing larger.'),
            image=test_image
        )
        ideal_project.save()
        ok_(ideal_project)

    def test_project_unicode(self):
        project = Project(title='Private Prisons')
        project.save()
        eq_(project.__unicode__(), u'Private Prisons')

    def test_add_contributors(self):
        user1 = User.objects.get(pk=1)
        user2 = User.objects.get(pk=2)
        project = Project(title='Private Prisons')
        project.save()
        project.contributors.add(user1, user2)
        ok_(user1 in project.contributors.all() and user2 in project.contributors.all())
