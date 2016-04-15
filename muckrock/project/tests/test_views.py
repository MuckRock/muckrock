"""
Projects are a way to quickly introduce our audience to the
topics and issues we cover and then provide them avenues for
deeper, sustained involvement with our work on those topics.
"""

from django.contrib.auth.models import User, AnonymousUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.http import Http404
from django.test import TestCase, Client, RequestFactory

from muckrock import factories
from muckrock.project import models, forms, views
from muckrock.utils import mock_middleware

import logging
import nose.tools

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_
raises = nose.tools.raises

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

def get_helper(view_, url_, user, **kwargs):
    """Helper to return a GET response."""
    request = RequestFactory().get(url_)
    request = mock_middleware(request)
    request.user = user
    response = view_(request, **kwargs)
    return response

def post_helper(view_, url_, data, user, **kwargs):
    """Helper to return a POST response."""
    request = RequestFactory().post(url_, data)
    request = mock_middleware(request)
    request.user = user
    response = view_(request, **kwargs)
    return response

class TestProjectCreateView(TestCase):
    """Tests creating a project as a user."""
    def setUp(self):
        self.view = views.ProjectCreateView.as_view()
        self.url = reverse('project-create')

    def test_staff(self):
        """Staff users should be able to GET the ProjectCreateView."""
        staff_user = factories.UserFactory(is_staff=True)
        response = get_helper(self.view, self.url, staff_user)
        eq_(response.status_code, 200,
            'Staff users should be able to GET the ProjectCreateView.')

    def test_experimental(self):
        """Experimental users should be able to GET the ProjectCreateView."""
        exp_user = factories.UserFactory(profile__experimental=True)
        response = get_helper(self.view, self.url, exp_user)
        eq_(response.status_code, 200,
            'Experimental users should be able to GET the ProjectCreateView.')

    def test_basic(self):
        """Basic users should not be able to GET the ProjectCreateView."""
        user = factories.UserFactory()
        response = get_helper(self.view, self.url, user)
        eq_(response.status_code, 302,
            'Basic users should not be able to GET the ProjectCreateView.')
        redirect_url = reverse('acct-login') + '?next=' + reverse('project-create')
        eq_(response.url, redirect_url,
            'The user should be redirected to the login page.')

    def test_anonymous(self):
        """Logged out users should not be able to GET the ProjectCreateView."""
        response = get_helper(self.view, self.url, AnonymousUser())
        eq_(response.status_code, 302,
            'Anonymous users should not be able to GET the ProjectCreateView.')
        redirect_url = reverse('acct-login') + '?next=' + reverse('project-create')
        eq_(response.url, redirect_url,
            'The user should be redirected to the login page.')

    def test_post(self):
        """Posting a valid ProjectForm should create the project."""
        form = forms.ProjectBasicsForm({
            'title': 'Cool Project',
            'summary': 'Yo my project is cooler than LIFE!',
            'image': test_image,
            'tags': 'dogs, cats',
            'private': True,
            'featured': True
        })
        ok_(form.is_valid(), 'The form should validate.')
        staff_user = factories.UserFactory(is_staff=True)
        response = post_helper(self.view, self.url, form.data, staff_user)
        project = models.Project.objects.last()
        eq_(response.status_code, 302,
            'The response should redirect to the project when it is created.')
        ok_(staff_user in project.contributors.all(),
            'The current user should automatically be added as a contributor.')


class TestProjectEditView(TestCase):
    """Contributors and staff may edit a project."""
    def setUp(self):
        # We will start with a project that's already been made.
        # We will give that project a single contributor.
        self.contributor = factories.UserFactory()
        self.project = factories.ProjectFactory()
        self.project.contributors.add(self.contributor)
        self.project.save()
        self.factory = RequestFactory()
        self.kwargs = {
            'slug': self.project.slug,
            'pk': self.project.pk
        }
        self.url = reverse('project-edit', kwargs=self.kwargs)
        self.view = views.ProjectEditView.as_view()

    def test_staff(self):
        """Staff users should be able to edit projects."""
        staff_user = factories.UserFactory(is_staff=True)
        response = get_helper(self.view, self.url, staff_user, **self.kwargs)
        eq_(response.status_code, 200)

    def test_contributor(self):
        """Contributors should be able to edit projects."""
        response = get_helper(self.view, self.url, self.contributor, **self.kwargs)
        eq_(response.status_code, 200)

    @raises(Http404)
    def test_basic(self):
        """Basic users should not be able to edit projects."""
        user = factories.UserFactory()
        response = get_helper(self.view, self.url, user, **self.kwargs)

    def test_anonymous(self):
        """Logged out users cannot edit projects."""
        response = get_helper(self.view, self.url, AnonymousUser())
        redirect_url = reverse('acct-login') + '?next=' + self.url
        eq_(response.status_code, 302,
            'The user should be redirected.')
        eq_(response.url, redirect_url,
            'The user should be redirected to the login page.')

    def test_edit_description(self):
        """
        The description should be editable.
        When sending data, the 'edit' keyword should be set to 'description'.
        """
        desc = 'Lorem ipsum'
        data = {
            'description': desc,
            'edit': 'description'
        }
        form = forms.ProjectUpdateForm(data)
        ok_(form.is_valid(), 'The form should validate. %s' % form.errors)
        response = post_helper(self.view, self.url, data, self.contributor, **self.kwargs)
        self.project.refresh_from_db()
        eq_(self.project.description, desc,
            'The description should be updated.')


class TestProjectDeleteView(TestCase):
    """Tests deleting a project as a user."""
    def setUp(self):
        # We will start with a project that's already been made.
        self.project = factories.ProjectFactory()
        self.contributor = factories.UserFactory()
        self.project.contributors.add(self.contributor)
        self.kwargs = {
            'slug': self.project.slug,
            'pk': self.project.pk
        }
        self.url = reverse('project-delete', kwargs=self.kwargs)
        self.view = views.ProjectDeleteView.as_view()

    def test_staff(self):
        """Staff users should be able to delete projects."""
        staff_user = factories.UserFactory(is_staff=True)
        response = get_helper(self.view, self.url, staff_user, **self.kwargs)
        eq_(response.status_code, 200)

    def test_contributor(self):
        """Contributors should be able to delete projects."""
        response = get_helper(self.view, self.url, self.contributor, **self.kwargs)
        eq_(response.status_code, 200)

    @raises(Http404)
    def test_basic(self):
        """Basic users should not be able to delete projects."""
        user = factories.UserFactory()
        response = get_helper(self.view, self.url, user, **self.kwargs)

    def test_anonymous(self):
        """Anonymous users cannot delete projects."""
        response = get_helper(self.view, self.url, AnonymousUser(), **self.kwargs)
        redirect_url = reverse('acct-login') + '?next=' + self.url
        eq_(response.status_code, 302,
            'The user should be redirected.')
        eq_(response.url, redirect_url,
            'The user should be reidrected to the login screen.')
