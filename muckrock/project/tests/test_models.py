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

import logging
import nose


ok_ = nose.tools.ok_
eq_ = nose.tools.eq_

test_title = u'Private Prisons'
test_description = (
    u'The prison industry is growing at an alarming rate. '
    'Even more alarming? The conditions inside prisions '
    'are growing worse while their tax-dollar derived '
    'profits are growing larger.')
test_image = SimpleUploadedFile(
    name='foo.gif',
    content=(b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,'
    '\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00'))

class TestProject(TestCase):
    """Projects are a mixture of general and specific information on a broad subject."""

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
        self.basic_project = Project(title=test_title)
        self.basic_project.save()

    def tearDown(self):
        self.basic_project.delete()

    def test_basic_project(self):
        """All projects need at least a title."""
        ok_(self.basic_project)

    def test_project_unicode(self):
        """Projects should default to printing their title."""
        eq_(self.basic_project.__unicode__(), test_title)

    def test_ideal_project(self):
        """
        Projects should have a statement describing their purpose
        and an image or illustration to accompany them.
        """
        ideal_project = self.basic_project
        ideal_project.description = test_description
        ideal_project.image = test_image
        ideal_project.save()
        ok_(ideal_project)

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

    def test_make_private(self):
        """Projects should be able to be made private."""
        project = self.basic_project
        ok_(not project.private)
        project.make_private()
        ok_(project.private)
        project.make_public()
        ok_(not project.private)

    def test_has_contributors(self):
        """Projects should test to see if a given user is a contributor."""
        project = self.basic_project
        user1 = User.objects.get(pk=1)
        user2 = User.objects.get(pk=2)
        project.contributors.add(user1)
        ok_(project.has_contributor(user1))
        ok_(not project.has_contributor(user2))

    def test_suggest_requests(self):
        """
        Projects should recommend requests to be added to them.
        They should recommend requests that intersect both the
        project's set of contributors and the project's set of tags.
        But projects should not recommend requests that they already contain.
        """
        # set up data
        tags = u'a'
        user = User.objects.get(pk=1)
        project = self.basic_project
        project.contributors.add(user)
        project.tags.add(tags)
        test_request = FOIARequest.objects.get(pk=1)
        test_request.user = user
        test_request.tags.add(tags)
        # since they have the same user and tags, the project should suggest the request
        ok_(test_request in project.suggest_requests())
        logging.debug(project.suggest_requests())
        # add the request to the project, then try again. it should not be suggested
        project.requests.add(test_request)
        ok_(test_request not in project.suggest_requests())
        logging.debug(project.suggest_requests())

    def test_suggest_articles(self):
        """
        Projects should recommend articles to be added to them.
        They should recommend articles that intersect both the
        project's set of contributors and the project's set of tags.
        But projects should not recommend articles that they already contain.
        """
        # set up data
        tags = u'a'
        user = User.objects.get(pk=1)
        project = self.basic_project
        project.contributors.add(user)
        project.tags.add(tags)
        test_article = Article.objects.get(pk=1)
        test_article.authors.add(user)
        test_article.tags.add(tags)
        # since they have the same user and tags, the project should suggest the article.
        ok_(test_article in project.suggest_articles())
        logging.debug(project.suggest_articles())
        # add the article to the project, then try again. it should not be suggested
        project.articles.add(test_article)
        ok_(test_article not in project.suggest_articles())
        logging.debug(project.suggest_articles())

class TestProjectTagging(TestCase):
    """Tests for the tagging feature of projects"""

    def setUp(self):
        self.basic_project = Project(title=test_title)
        self.basic_project.save()

    def test_add_tags(self):
        """Projects should keep a list of relevant tags."""
        project = self.basic_project
        eq_(len(project.tags.all()), 0)
        project.tags.add(u'prison', u'privatization', u'corrections')
        eq_(len(project.tags.all()), 3)

    def test_add_existing_tags(self):
        """Projects should not contain duplicate tags."""
        project = self.basic_project
        eq_(len(project.tags.all()), 0)
        project.tags.add(u'prison', u'privatization', u'corrections')
        project.tags.add(u'prison', u'privatization', u'corrections')
        eq_(len(project.tags.all()), 3)

    def test_remove_existing_tag(self):
        """Tags should be easily removed from projects."""
        project = self.basic_project
        eq_(len(project.tags.all()), 0)
        project.tags.add(u'prison', u'privatization', u'corrections')
        eq_(len(project.tags.all()), 3)
        project.tags.remove(u'prison')
        eq_(len(project.tags.all()), 2)

    def test_remove_nonexisting_tag(self):
        """Nonexisting tags cannot be removed from a project."""
        project = self.basic_project
        eq_(len(project.tags.all()), 0)
        project.tags.add(u'prison', u'privatization', u'corrections')
        eq_(len(project.tags.all()), 3)
        project.tags.remove(u'spongebob')
        eq_(len(project.tags.all()), 3)
