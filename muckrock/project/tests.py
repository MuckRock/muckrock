"""
Projects are a way to quickly introduce our audience to the
topics and issues we cover and then provide them avenues for
deeper, sustained involvement with our work on those topics.
"""

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from muckrock.foia.models import FOIARequest
from muckrock.news.models import Article
from muckrock.project.models import Project

import nose

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_

"""
* Projects must have a title.
* Projects should have a statement describing their purpose.
* Projects should have an image or illustration to accompany them.
* Projects should keep a list of relevant requests.
* Projects should keep a list of relevant articles.
* Projects should keep a list of relevant keywords/tags.
* Projects should be kept very flexible and nonprescritive.
* Projects should be able to be made private.
"""

class TestProject(TestCase):

    fixtures = [
        'test_users.json',
        'test_profiles.json',
        'test_news.json',
        'test_foiarequests.json',
        'test_agencies.json',
        'agency_types.json',
        'jurisdictions.json',
        'holidays.json'
    ]

    def setUp(self):
        self.basic_project = Project(title='Private Prisons')
        self.basic_project.save()

    def test_basic_project(self):
        """All projects need at least a title."""
        ok_(self.basic_project)

    def test_ideal_project(self):
        """
        Projects should have a statement describing their purpose
        and an image or illustration to accompany them.
        """
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
        """
        A project should keep a list of contributors,
        but a list of contributors should not be required.
        """
        project = self.basic_project
        user1 = User.objects.get(pk=1)
        user2 = User.objects.get(pk=2)
        project.contributors.add(user1, user2)
        ok_(user1 in project.contributors.all() and user2 in project.contributors.all())
        project.contributors.clear()
        eq_(len(project.contributors.all()), 0)

    def test_add_articles(self):
        """Projects should keep a list of relevant articles."""
        project = self.basic_project
        article1 = Article.objects.get(pk=1)
        article2 = Article.objects.get(pk=2)
        project.articles.add(article1, article2)
        ok_(article1 in project.articles.all())
        ok_(article2 in project.articles.all())
        project.articles.clear()
        eq_(len(project.articles.all()), 0)

    def test_add_requests(self):
        """Projects should keep a list of relevant FOIA requests."""
        project = self.basic_project
        request1 = FOIARequest.objects.get(pk=1)
        request2 = FOIARequest.objects.get(pk=2)
        project.requests.add(request1, request2)
        ok_(request1 in project.requests.all())
        ok_(request2 in project.requests.all())
        project.articles.clear()
        eq_(len(project.articles.all()), 0)
