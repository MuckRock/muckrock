"""
Projects are a way to quickly introduce our audience to the
topics and issues we cover and then provide them avenues for
deeper, sustained involvement with our work on those topics.
"""

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.test import TestCase, Client

from muckrock.project.models import Project
from muckrock.project.forms import ProjectCreateForm, ProjectUpdateForm

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
        self.url = reverse('project-create')

    def tearDown(self):
        self.client.logout()

    def test_create_project_functional(self):
        """I want to create a project."""
        # First things first I need to be logged in
        self.client.login(username='adam', password='abc')
        # I point my browser at the right webpage
        response = self.client.get(self.url)
        eq_(response.status_code, 200,
            'Should load page to create a new project.')
        ok_(isinstance(response.context['form'], ProjectCreateForm),
            'Should load page with a ProjectCreateForm')
        # Then I fill out a form with all the details of my project.
        project_title = test_title
        project_description = test_description
        # project_image = test_image
        new_project_form = ProjectCreateForm({
            'title': project_title,
            'description': project_description,
            # 'image': project_image
        })
        logging.debug('The form is valid: %s.', new_project_form.is_valid())
        eq_(Project.objects.count(), 0, 'There should be no projects.')
        logging.debug('Projects: %s', Project.objects.all())
        # When I submit the form, I expect the project to be made and to be redirected to it.
        response = self.client.post(self.url, new_project_form.data, follow=False)
        logging.debug('POST data: %s', new_project_form.data)
        logging.debug('POST URL: %s', self.url)
        logging.debug('POST status code: %s', response.status_code)
        logging.debug('There are %s projects.', Project.objects.count())
        logging.debug('Projects: %s', Project.objects.all())
        eq_(Project.objects.count(), 1, 'There should now be one project.')
        # An action should also be created with this project as the target
        Project.objects.first()
        logging.debug('Projects: %s', Project.objects.all())
        eq_(response.status_code, 302,
            'Should redirect to the newly created project.')
        self.assertRedirects(response, list(Project.objects.all())[-1].get_absolute_url())

    def test_requires_login(self):
        """Logged out users cannot create projects."""
        response = self.client.get(self.url)
        redirect_url = reverse('acct-login') + '?next=' + reverse('project-create')
        self.assertRedirects(response, redirect_url)

    def test_staff_only(self):
        """For now, staff are the only ones who can create new projects."""
        staff_user = User.objects.get(username='adam')
        nonstaff_user = User.objects.get(username='bob')
        ok_(staff_user.is_staff and not nonstaff_user.is_staff)
        staff_client = Client()
        staff_client.login(username='adam', password='abc')
        staff_response = staff_client.get(self.url)
        ok_(staff_response.status_code is 200)
        nonstaff_client = Client()
        nonstaff_client.login(username='bob', password='abc')
        nonstaff_response = nonstaff_client.get(self.url)
        ok_(nonstaff_response.status_code is not 200,
            'Nonstaff users should not be able to create a new project at this time.')

    def test_creator_made_contributor(self):
        """The creation form should set the current user as a contributor by default."""
        self.client.login(username='adam', password='abc')
        response = self.client.get(self.url)
        project_create_form = response.context['form']
        ok_(User.objects.get(username='adam') in project_create_form.initial['contributors'],
            'Current user should be an initial value for the contributors field')

def staff_and_contributors_only(project, project_url, action='load'):
    """Tests that only staff and contributors can access a given URL."""
    client = Client()
    staff_user = User.objects.get(username='adam')
    contributor_user = User.objects.get(username='bob')
    nonstaff_noncontributor_user = User.objects.get(username='basic')
    # set the contributor as a contributor
    project.contributors.add(contributor_user)
    # test that all users have the expected permissions
    ok_(staff_user.is_staff)
    ok_(contributor_user in project.contributors.all() and not contributor_user.is_staff)
    ok_(not nonstaff_noncontributor_user.is_staff and \
        nonstaff_noncontributor_user not in project.contributors.all())
    # try accessing as a staff user
    client.login(username='adam', password='abc')
    response = client.get(project_url)
    ok_(response.status_code is 200, 'Staff should be able to ' + action + ' the project.')
    client.logout()
    # try accessing as a contributor
    client.login(username='bob', password='abc')
    response = client.get(project_url)
    ok_(response.status_code is 200, 'Contributors should be able to ' + action + ' the project.')
    client.logout()
    # try accessing as a nonstaff noncontributor
    client.login(username='basic', password='abc')
    response = client.get(project_url)
    ok_(response.status_code is not 200,
        'Nonstaff-noncontributors should not be able to ' + action + ' the project.')
    client.logout()

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
        self.url = self.project.get_absolute_url() + 'update/'
        # I will start by logging in.
        self.user = Client()
        self.user.login(username='adam', password='abc')

    def tearDown(self):
        self.project.delete()
        self.user.logout()

    def test_update_project_functional(self):
        """I want to update a project that I've already made."""
        # First I go to the page for updating the project.
        response = self.user.get(self.url)
        eq_(response.status_code, 200,
            'The page for updating the project should load.')
        ok_(isinstance(response.context['form'], ProjectUpdateForm),
            'The page should contain a form for updating the project.')
        eq_(response.context['form'].instance, self.project,
            'The form on the page should reflect my project instance.')
        # Then I want to update the description of the project to something new.
        new_description = u'This is the greatest project of all time!'
        project_update_form = ProjectUpdateForm({
            'description': new_description
        }, instance=self.project)
        ok_(project_update_form.is_valid(), 'The project form should validate.')
        # Then I submit the form with my updated information.
        response = self.user.post(self.url, project_update_form.data)
        # I expect to be redirected back to the project.
        eq_(response.status_code, 302,
            'Should redirect after submitting the update form.')
        self.assertRedirects(response, self.project.get_absolute_url())
        # I expect the project to reflect my update.
        updated_project = Project.objects.get(id=self.project.id)
        eq_(updated_project.description, new_description,
            'The updates to the project should be saved.')

    def test_requires_login(self):
        """Logged out users cannot update projects."""
        response = self.client.get(self.url)
        redirect_url = reverse('acct-login') + '?next=' + self.url
        self.assertRedirects(response, redirect_url)

    def test_staff_or_contributor_only(self):
        """Projects should only be updated by staff or project contributors."""
        staff_and_contributors_only(self.project, self.url, 'update')


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
        self.url = self.project.get_absolute_url() + 'delete/'
        # I will start by logging in.
        self.user = Client()
        self.user.login(username='adam', password='abc')

    def tearDown(self):
        self.user.logout()
        self.project.delete()

    @nose.tools.raises(Project.DoesNotExist)
    def test_delete_project_functional(self):
        """I want to delete a project that I've already made."""
        # First I go to the page for deleting a project instance.
        response = self.user.get(self.url)
        eq_(response.status_code, 200,
            'The page for deleting a project should load.')
        # I am really, absolutely sure I want to delete this project!
        response = self.user.post(self.url)
        deleted_project = Project.objects.get(id=self.project.id)
        # Poof! Goodbye, project!
        ok_(not deleted_project, 'The project should be deleted.')
        eq_(response.status_code, 302,
            'The page should redirect after deleting the project.')
        self.assertRedirects(response, reverse('index'))

    def test_requires_login(self):
        """Logged out users cannot delete projects."""
        response = self.client.get(self.url)
        redirect_url = reverse('acct-login') + '?next=' + self.url
        self.assertRedirects(response, redirect_url)

    def test_staff_or_contributor_only(self):
        """Projects should only be deleted by staff or project contributors."""
        staff_and_contributors_only(self.project, self.url, 'delete')
