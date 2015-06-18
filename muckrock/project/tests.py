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
from muckrock.project.forms import ProjectCreateForm, ProjectUpdateForm

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

class TestProjectCreateView(TestCase):
    """Tests creating a project as a user."""

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

    def test_create_project_functional(self):
        """I want to create a project."""
        # First things first I need to be logged in
        self.client.login(username='adam', password='abc')
        # I point my browser at the right webpage
        response = self.client.get(reverse('project-create'))
        eq_(response.status_code, 200,
            'Should load page to create a new project.')
        eq_(type(response.context['form']), type(ProjectCreateForm()),
            'Should load page with a ProjectCreateForm')
        # Then I fill out a form with all the details of my project.
        project_title = test_title
        project_description = test_description
        project_image = test_image
        new_project_form = ProjectCreateForm({
            'title': project_title,
            'description': project_description,
            'image': project_image
        })
        # When I submit the form, I expect the project to be made and to be redirected to it.
        response = self.client.post(reverse('project-create'), new_project_form.data)
        new_project = Project.objects.get(title=project_title)
        ok_(new_project, 'Should create the project.')
        eq_(response.status_code, 302,
            'Should redirect to the newly created project.')
        self.assertRedirects(response, new_project.get_absolute_url())

    def test_create_project_requires_login(self):
        """Logged out users cannot create projects."""
        response = self.client.get(reverse('project-create'))
        redirect_url = reverse('acct-login') + '?next=' + reverse('project-create')
        self.assertRedirects(response, redirect_url)

class TestProjectUpdateView(TestCase):
    """Tests updating a project as a user."""

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
        # We will start with a project that's already been made.
        self.project = Project.objects.create(
            title=test_title,
            description=test_description,
            image=test_image
        )
        self.project.save()
        # I will start by logging in.
        self.user = Client()
        self.user.login(username='adam', password='abc')

    def test_update_project_functional(self):
        """I want to update a project that I've already made."""
        # First I go to the page for updating the project.
        project_update_url = self.project.get_absolute_url() + 'update/'
        response = self.user.get(project_update_url)
        eq_(response.status_code, 200,
            'The page for updating the project should load.')
        eq_(type(response.context['form']), type(ProjectUpdateForm()),
            'The page should contain a form for updating the project.')
        eq_(response.context['form'].instance, self.project,
            'The form on the page should reflect my project instance.')
        # Then I want to update the description of the project to something new.
        new_description = u'This is the greatest project of all time!'
        project_update_form = ProjectUpdateForm({
            'description': new_description
        }, instance=self.project)
        # Then I submit the form with my updated information.
        response = self.user.post(project_update_url, project_update_form.data)
        # I expect to be redirected back to the project.
        eq_(response.status_code, 302,
            'Should redirect after submitting the update form.')
        self.assertRedirects(response, self.project.get_absolute_url())
        # I expect the project to reflect my update.
        updated_project = Project.objects.get(id=self.project.id)
        eq_(updated_project.description, new_description,
            'The updates to the project should be saved.')

    def test_create_project_requires_login(self):
        """Logged out users cannot update projects."""
        project_update_url = self.project.get_absolute_url() + 'update/'
        response = self.client.get(project_update_url)
        redirect_url = reverse('acct-login') + '?next=' + project_update_url
        self.assertRedirects(response, redirect_url)

class TestProjectDeleteView(TestCase):
    """Tests deleting a project as a user."""

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
        # We will start with a project that's already been made.
        self.project = Project.objects.create(
            title=test_title,
            description=test_description,
            image=test_image
        )
        self.project.save()
        # I will start by logging in.
        self.user = Client()
        self.user.login(username='adam', password='abc')

    @nose.tools.raises(Project.DoesNotExist)
    def test_delete_project_functional(self):
        """I want to delete a project that I've already made."""
        # First I go to the page for deleting a project instance.
        project_delete_url = self.project.get_absolute_url() + 'delete/'
        response = self.user.get(project_delete_url)
        eq_(response.status_code, 200,
            'The page for deleting a project should load.')
        # I am really, absolutely sure I want to delete this project!
        response = self.user.post(project_delete_url)
        deleted_project = Project.objects.get(id=self.project.id)
        # Poof! Goodbye, project!
        ok_(not deleted_project, 'The project should be deleted.')
        eq_(response.status_code, 302,
            'The page should redirect after deleting the project.')
        self.assertRedirects(response, reverse('index'))

    def test_create_project_requires_login(self):
        """Logged out users cannot update projects."""
        project_delete_url = self.project.get_absolute_url() + 'delete/'
        response = self.client.get(project_delete_url)
        redirect_url = reverse('acct-login') + '?next=' + project_delete_url
        self.assertRedirects(response, redirect_url)
