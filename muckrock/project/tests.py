"""
Projects are a way to quickly introduce our audience to the
topics and issues we cover and then provide them avenues for
deeper, sustained involvement with our work on those topics.
"""

from django.core.files import File
from django.test import TestCase
import mock
from muckrock.news.models import Photo
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

    def test_create_new_project(self):
        """
        Create a new project:
        * Projects must have a title.
        * Projects should have a statement describing their purpose.
        * Projects should have an image or illustration to accompany them.
        """
        minimum_project = Project(title='Private Prisons')
        ok_(minimum_project)
        ideal_project = Project(
            title='Private Prisons',
            description=('The prison industry is growing at an alarming rate. '
                        'Even more alarming? The conditions inside prisions '
                        'are growing worse while their tax-dollar derived '
                        'profits are growing larger.'),
            image=mock.MagicMock(spec=File, name='FileMock')
        )
        ok_(ideal_project)

    def test_project_unicode(self):
        project = Project(title='Private Prisons')
        eq_(project.__unicode__(), u'Private Prisons')


