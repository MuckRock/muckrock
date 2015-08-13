"""
Test FOIA application forms
"""

from django import test

from nose.tools import eq_, ok_

from muckrock.foia.forms import FOIAAdminFixForm

class TestAdminFixForm(test.TestCase):
    """Test data cleaning methods on admin fix form"""

    def test_email_cleaning(self):
        """The email addresses should be stripped of extra white space."""
        data = {
            'from_email': 'tester@tester.com',
            'email': 'extra@space.com ',
            'comm': 'Test'
        }
        form = FOIAAdminFixForm(data)
        ok_(form.is_valid(), 'The form should validate')
        eq_(form.cleaned_data['email'], 'extra@space.com',
            'Extra space should be stripped from the email address.')
