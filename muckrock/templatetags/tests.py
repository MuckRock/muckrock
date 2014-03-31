"""
Tests using nose for the templatetags
"""

from django.test import TestCase

import nose.tools
from mock import Mock

from muckrock.templatetags.templatetags import tags

# allow methods that could be functions and too many public methods in tests
# pylint: disable=R0201
# pylint: disable=R0904

class TestTemplatetagsFunctional(TestCase):
    """Functional tests for templatetags"""

    def test_active(self):
        """Test the active template tag"""
        mock_request = Mock()
        mock_request.user = 'adam'
        mock_request.path = '/test1/adam/'

        nose.tools.eq_(tags.active(mock_request, '/test1/{{user}}/'), 'current-tab')
        nose.tools.eq_(tags.active(mock_request, '/test2/{{user}}/'), '')

    def test_page_links(self):
        """Test the page_links template tag"""
        mock_page_obj = Mock()
        mock_page_obj.number = 5
        mock_page_obj.paginator.num_pages = 10

        links = '&hellip;&nbsp;' + \
                ''.join('<a href="?page=%d">%d</a>&nbsp;&nbsp;' % (i, i) for i in range(2, 5)) + \
                '5' + \
                ''.join('&nbsp;&nbsp;<a href="?page=%d">%d</a>' % (i, i) for i in range(6, 9)) + \
                '&nbsp;&hellip;'

        nose.tools.eq_(tags.page_links(mock_page_obj, None, None), links)

    def test_company_title(self):
        """Test the company_title template tag"""

        nose.tools.eq_(tags.company_title('one\ntwo\nthree'), 'one, et al')
        nose.tools.eq_(tags.company_title('company'), 'company')

