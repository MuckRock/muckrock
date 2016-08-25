"""
Projects are a way to quickly introduce our audience to the
topics and issues we cover and then provide them avenues for
deeper, sustained involvement with our work on those topics.
"""

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from muckrock.factories import (
        ProjectFactory,
        UserFactory,
        ArticleFactory,
        FOIARequestFactory,
        )

from muckrock.foia.models import FOIARequest
from muckrock.news.models import Article
from muckrock.project.models import Project
from muckrock.task.models import ProjectReviewTask

import logging
from nose.tools import (
        ok_,
        eq_,
        assert_in,
        assert_not_in,
        assert_false,
        assert_is_instance,
        )


class TestProject(TestCase):
    """Projects are a mixture of general and specific information on a broad subject."""

    def test_project_unicode(self):
        """Projects should default to printing their title."""
        project = ProjectFactory()
        eq_(unicode(project), project.title)

    def test_ideal_project(self):
        """
        Projects should have a statement describing their purpose
        and an image or illustration to accompany them.
        """
        test_description = (
            u'The prison industry is growing at an alarming rate. '
            'Even more alarming? The conditions inside prisions '
            'are growing worse while their tax-dollar derived '
            'profits are growing larger.')
        test_image = SimpleUploadedFile(
            name='foo.gif',
            content=(b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,'
            '\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00'))
        ideal_project = ProjectFactory(
                description=test_description,
                image=test_image)
        ok_(ideal_project)

    def test_add_contributors(self):
        """
        A project should keep a list of contributors,
        but a list of contributors should not be required.
        """
        project = ProjectFactory()
        users = UserFactory.create_batch(2)
        project.contributors.add(*users)
        assert_in(users[0], project.contributors.all())
        assert_in(users[1], project.contributors.all())
        project.contributors.clear()
        eq_(len(project.contributors.all()), 0)

    def test_add_articles(self):
        """Projects should keep a list of relevant articles."""
        project = ProjectFactory()
        articles = ArticleFactory.create_batch(2)
        project.articles.add(*articles)
        assert_in(articles[0], project.articles.all())
        assert_in(articles[1], project.articles.all())
        project.articles.clear()
        eq_(len(project.articles.all()), 0)

    def test_add_requests(self):
        """Projects should keep a list of relevant FOIA requests."""
        project = ProjectFactory()
        requests = FOIARequestFactory.create_batch(2)
        project.requests.add(*requests)
        assert_in(requests[0], project.requests.all())
        assert_in(requests[1], project.requests.all())
        project.articles.clear()
        eq_(len(project.articles.all()), 0)

    def test_private(self):
        """Projects should be private by default."""
        project = ProjectFactory()
        ok_(project.private)

    def test_make_public(self):
        """Projects can be made public, but they shouldn't be approved."""
        project = ProjectFactory()
        ok_(project.private)
        project.make_public()
        assert_false(project.private)
        assert_false(project.approved)

    def test_has_contributors(self):
        """Projects should test to see if a given user is a contributor."""
        project = ProjectFactory()
        users = UserFactory.create_batch(2)
        project.contributors.add(users[0])
        ok_(project.has_contributor(users[0]))
        assert_false(project.has_contributor(users[1]))

    def test_editable_by(self):
        """Projects should test to see if a given user can edit a request."""
        project = ProjectFactory()
        users = UserFactory.create_batch(2)
        project.contributors.add(users[0])
        ok_(project.editable_by(users[0]))
        assert_false(project.editable_by(users[1]))

    def test_publish(self):
        """Publishing a project should make it public and submit it for approval."""
        project = ProjectFactory()
        task = project.publish('Test')
        assert_false(project.private, 'The project should be made public.')
        assert_false(project.approved, 'The project should be waiting approval.')
        assert_is_instance(task, ProjectReviewTask,
            'A ProjectReviewTask should be created.\n\tTask: %s' % type(task))

    def test_suggest_requests(self):
        """
        Projects should recommend requests to be added to them.
        They should recommend requests that intersect both the
        project's set of contributors and the project's set of tags.
        But projects should not recommend requests that they already contain.
        """
        # set up data
        tags = (u'a',)
        user = UserFactory()
        project = ProjectFactory(tags=tags)
        project.contributors.add(user)
        test_request = FOIARequestFactory(user=user, tags=tags)
        # since they have the same user and tags, the project should suggest the request
        assert_in(test_request, project.suggest_requests())
        logging.debug(project.suggest_requests())
        # add the request to the project, then try again. it should not be suggested
        project.requests.add(test_request)
        assert_not_in(test_request, project.suggest_requests())
        logging.debug(project.suggest_requests())

    def test_suggest_articles(self):
        """
        Projects should recommend articles to be added to them.
        They should recommend articles that intersect both the
        project's set of contributors and the project's set of tags.
        But projects should not recommend articles that they already contain.
        """
        # set up data
        tags = (u'a',)
        user = UserFactory()
        project = ProjectFactory(tags=tags)
        project.contributors.add(user)
        test_article = ArticleFactory(tags=tags)
        test_article.authors.add(user)
        # since they have the same user and tags, the project should suggest the article.
        assert_in(test_article, project.suggest_articles())
        logging.debug(project.suggest_articles())
        # add the article to the project, then try again. it should not be suggested
        project.articles.add(test_article)
        assert_not_in(test_article, project.suggest_articles())
        logging.debug(project.suggest_articles())


class TestProjectTagging(TestCase):
    """Tests for the tagging feature of projects"""

    def test_add_tags(self):
        """Projects should keep a list of relevant tags."""
        project = ProjectFactory()
        eq_(len(project.tags.all()), 0)
        project.tags.add(u'prison', u'privatization', u'corrections')
        eq_(len(project.tags.all()), 3)

    def test_add_existing_tags(self):
        """Projects should not contain duplicate tags."""
        project = ProjectFactory()
        eq_(len(project.tags.all()), 0)
        project.tags.add(u'prison', u'privatization', u'corrections')
        project.tags.add(u'prison', u'privatization', u'corrections')
        eq_(len(project.tags.all()), 3)

    def test_remove_existing_tag(self):
        """Tags should be easily removed from projects."""
        project = ProjectFactory()
        eq_(len(project.tags.all()), 0)
        project.tags.add(u'prison', u'privatization', u'corrections')
        eq_(len(project.tags.all()), 3)
        project.tags.remove(u'prison')
        eq_(len(project.tags.all()), 2)

    def test_remove_nonexisting_tag(self):
        """Nonexisting tags cannot be removed from a project."""
        project = ProjectFactory()
        eq_(len(project.tags.all()), 0)
        project.tags.add(u'prison', u'privatization', u'corrections')
        eq_(len(project.tags.all()), 3)
        project.tags.remove(u'spongebob')
        eq_(len(project.tags.all()), 3)
