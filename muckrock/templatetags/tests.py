"""
Tests using nose for the templatetags
"""

# Django
from django.test import TestCase

# Third Party
import nose.tools
from mock import Mock

# MuckRock
from muckrock.templatetags.templatetags import tags


class TestTemplatetagsFunctional(TestCase):
    """Functional tests for templatetags"""

    def test_active(self):
        """Test the active template tag"""
        mock_request = Mock()
        mock_request.user = 'adam'
        mock_request.path = '/test1/adam/'

        nose.tools.eq_(
            tags.active(mock_request, '/test1/{{user}}/'), 'current-tab'
        )
        nose.tools.eq_(tags.active(mock_request, '/test2/{{user}}/'), '')

    def test_company_title(self):
        """Test the company_title template tag"""

        nose.tools.eq_(tags.company_title('one\ntwo\nthree'), 'one, et al')
        nose.tools.eq_(tags.company_title('company'), 'company')
