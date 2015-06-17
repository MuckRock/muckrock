"""
Projects are a way to quickly introduce our audience to the
topics and issues we cover and then provide them avenues for
deeper, sustained involvement with our work on those topics.
"""

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.test import TestCase, Client

from muckrock.foia.models import FOIARequest
from muckrock.news.models import Article
from muckrock.project.models import Project
from muckrock.project.forms import CreateProjectForm

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
        ideal_project = Project(
            title=test_title,
            description=test_description,
            image=test_image
        )
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

    def test_add_tags(self):
        """Projects should keep a list of relevant tags."""
        project = self.basic_project
        eq_(len(project.tags.all()), 0)
        project.tags.add(u'prison', u'privatization', u'corrections')
        eq_(len(project.tags.all()), 3)

    def test_make_private(self):
        """Projects should be able to be made private."""
        project = self.basic_project
        ok_(not project.private)
        project.make_private()
        ok_(project.private)
        project.make_public()
        ok_(not project.private)

class TestProjectViews(TestCase):
    """Project views allow projects to be created, displayed, and edited."""

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
        self.client = Client()

    def test_create_project(self):
        """I want to create a project."""
        # First things first I need to be logged in
        self.client.login(username='adam', password='abc')
        # I point my browser at the right webpage
        new_project_url = reverse('project-create')
        response = self.client.get(new_project_url)
        eq_(response.status_code, 200,
            'Should load page to create a new project. CODE: %d' % response.status_code)
        eq_(type(response.context['form']), type(CreateProjectForm()),
            'Should load page with a CreateProjectForm')
        # Then I fill out a form with all the details of my project.
        project_title = test_title
        project_description = test_description
        project_tags = u'prison, privatization, corrections'
        project_image = test_image
        project_contributors = [User.objects.get(pk=2), User.objects.get(pk=3)]
        project_make_me_a_contributor = True
        new_project_form = CreateProjectForm({
            'title': project_title,
            'description': project_description,
            'image': project_image
        })
        # When I submit the form, I expect the project to be made and to be redirected to it.
        response = self.client.post(reverse('project-create'), new_project_form.data)
        eq_(Project.objects.filter(title=project_title).count(), 1,
            'Should create the project.')
        eq_(response.status_code, 302,
            'Should redirect after submitting NewProjectForm.')
        eq_(response.redirect_url, '/project/' + slugify(project_title),
            'Should redirect to the page for the newly created project')
