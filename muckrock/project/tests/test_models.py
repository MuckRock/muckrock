"""
Projects are a way to quickly introduce our audience to the
topics and issues we cover and then provide them avenues for
deeper, sustained involvement with our work on those topics.
"""

# Django
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

# MuckRock
from muckrock.core.factories import ArticleFactory, ProjectFactory, UserFactory
from muckrock.foia.factories import FOIARequestFactory
from muckrock.task.models import ProjectReviewTask

test_title = "Private Prisons"
test_summary = "The private prison project is fanstastic."
test_description = (
    "The prison industry is growing at an alarming rate. "
    "Even more alarming? The conditions inside prisions "
    "are growing worse while their tax-dollar derived "
    "profits are growing larger."
)
test_image = SimpleUploadedFile(
    name="foo.gif",
    content=(
        b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,"
        b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00"
    ),
)


class TestProject(TestCase):
    """Projects are a mixture of general and specific information on a broad subject."""

    def setUp(self):
        self.project = ProjectFactory(title=test_title)

    def test_project_attributes(self):
        """
        All projects need at least a title.
        Projects should be private by default.
        Projects should be unapproved by default.
        Projects should have a statement describing their purpose
        and an image or illustration to accompany them.
        """
        assert self.project
        assert self.project.title == test_title
        assert self.project.private
        assert not self.project.approved
        self.project.summary = test_summary
        self.project.description = test_description
        self.project.image = test_image
        self.project.save()
        assert self.project

    def test_project_unicode(self):
        """Projects should default to printing their title."""
        assert str(self.project) == test_title

    def test_contributors(self):
        """
        A project should keep a list of contributors,
        but a list of contributors should not be required.
        """
        user1 = UserFactory()
        user2 = UserFactory()
        self.project.contributors.add(user1, user2)
        assert (
            user1 in self.project.contributors.all()
            and user2 in self.project.contributors.all()
        )
        self.project.contributors.clear()
        assert len(self.project.contributors.all()) == 0

    def test_articles(self):
        """Projects should keep a list of relevant articles."""
        article1 = ArticleFactory()
        article2 = ArticleFactory()
        self.project.articles.add(article1, article2)
        assert article1 in self.project.articles.all()
        assert article2 in self.project.articles.all()
        self.project.articles.clear()
        assert len(self.project.articles.all()) == 0

    def test_requests(self):
        """Projects should keep a list of relevant FOIA requests."""
        request1 = FOIARequestFactory()
        request2 = FOIARequestFactory()
        self.project.requests.add(request1, request2)
        assert request1 in self.project.requests.all()
        assert request2 in self.project.requests.all()
        self.project.articles.clear()
        assert len(self.project.articles.all()) == 0

    def test_make_public(self):
        """Projects can be made public, but they shouldn't be approved."""
        self.project.make_public()
        assert not self.project.private
        assert not self.project.approved

    def test_has_contributors(self):
        """Projects should test to see if a given user is a contributor."""
        user1 = UserFactory()
        user2 = UserFactory()
        self.project.contributors.add(user1)
        assert self.project.has_contributor(user1)
        assert not self.project.has_contributor(user2)

    def test_editable_by(self):
        """Projects should test to see if a given user can edit a request."""
        user1 = UserFactory()
        user2 = UserFactory()
        self.project.contributors.add(user1)
        assert self.project.editable_by(user1)
        assert not self.project.editable_by(user2)

    def test_publish(self):
        """Publishing a project should make it public and submit it for approval."""
        explanation = "Test"
        task = self.project.publish(explanation)
        assert not self.project.private, "The project should be made public."
        assert not self.project.approved, "The project should be waiting approval."
        assert isinstance(
            task, ProjectReviewTask
        ), "A ProjectReviewTask should be created.\n\tTask: %s" % type(task)

    def test_suggest_requests(self):
        """
        Projects should recommend requests to be added to them.
        They should recommend requests that intersect both the
        project's set of contributors and the project's set of tags.
        But projects should not recommend requests that they already contain.
        """
        # set up data
        tags = "a"
        user = UserFactory()
        self.project.contributors.add(user)
        self.project.tags.add(tags)
        test_request = FOIARequestFactory(composer__user=user)
        test_request.tags.add(tags)
        # since they have the same user and tags, the project should suggest the request
        assert test_request in self.project.suggest_requests()
        # add the request to the project, then try again. it should not be suggested
        self.project.requests.add(test_request)
        assert test_request not in self.project.suggest_requests()

    def test_suggest_articles(self):
        """
        Projects should recommend articles to be added to them.
        They should recommend articles that intersect both the
        project's set of contributors and the project's set of tags.
        But projects should not recommend articles that they already contain.
        """
        # set up data
        tags = "a"
        user = UserFactory()
        self.project.contributors.add(user)
        self.project.tags.add(tags)
        test_article = ArticleFactory()
        test_article.authors.add(user)
        test_article.tags.add(tags)
        # since they have the same user and tags, the project should suggest
        # the article.
        assert test_article in self.project.suggest_articles()
        # add the article to the project, then try again. it should not be suggested
        self.project.articles.add(test_article)
        assert test_article not in self.project.suggest_articles()


class TestProjectTagging(TestCase):
    """Tests for the tagging feature of projects"""

    def setUp(self):
        self.project = ProjectFactory()

    def test_add_tags(self):
        """Projects should keep a list of relevant tags."""
        assert len(self.project.tags.all()) == 0
        self.project.tags.add("prison", "privatization", "corrections")
        assert len(self.project.tags.all()) == 3

    def test_add_existing_tags(self):
        """Projects should not contain duplicate tags."""
        assert len(self.project.tags.all()) == 0
        self.project.tags.add("prison", "privatization", "corrections")
        self.project.tags.add("prison", "privatization", "corrections")
        assert len(self.project.tags.all()) == 3

    def test_remove_existing_tag(self):
        """Tags should be easily removed from projects."""
        assert len(self.project.tags.all()) == 0
        self.project.tags.add("prison", "privatization", "corrections")
        assert len(self.project.tags.all()) == 3
        self.project.tags.remove("prison")
        assert len(self.project.tags.all()) == 2

    def test_remove_nonexisting_tag(self):
        """Nonexisting tags cannot be removed from a project."""
        assert len(self.project.tags.all()) == 0
        self.project.tags.add("prison", "privatization", "corrections")
        assert len(self.project.tags.all()) == 3
        self.project.tags.remove("spongebob")
        assert len(self.project.tags.all()) == 3
