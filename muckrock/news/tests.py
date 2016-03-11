"""
Tests using nose for the news application
"""

from django.core.urlresolvers import reverse
from django.test import TestCase

import nose.tools
from datetime import datetime

from muckrock.news.models import Article
from muckrock.tests import get_allowed, get_404

# pylint: disable=no-self-use
# pylint: disable=too-many-public-methods

class TestNewsUnit(TestCase):
    """Unit tests for news"""
    fixtures = ['test_users.json', 'test_news.json']

    def setUp(self):
        """Set up tests"""
        self.article = Article.objects.get(pk=1)

    # models
    def test_article_model_unicode(self):
        """Test the Article model's __unicode__ method"""
        nose.tools.eq_(unicode(self.article), 'Test Article 1')

    def test_article_model_url(self):
        """Test the Article model's get_absolute_url method"""
        nose.tools.eq_(self.article.get_absolute_url(), reverse(
            'news-detail',
            kwargs={'year': 1984, 'month': 'dec', 'day': 29, 'slug': 'test-article-1'}
        ))

    # manager
    def test_manager_get_published(self):
        """Test the Article Manager's get_punlished method"""
        nose.tools.ok_(all(a.publish and a.pub_date <= datetime.now()
                           for a in Article.objects.get_published()))
        nose.tools.eq_(len(Article.objects.get_published()), 5)

    def test_manager_get_drafts(self):
        """Test the Article Manager's get_drafts method"""
        nose.tools.ok_(all(not a.publish for a in Article.objects.get_drafts()))
        nose.tools.eq_(len(Article.objects.get_drafts()), 2)


class TestNewsFunctional(TestCase):
    """Functional tests for news"""
    fixtures = ['test_users.json', 'test_news.json']

    # views
    def test_news_index(self):
        """Should redirect to list"""
        get_allowed(self.client, reverse('news-index'))

    def test_news_archive_year(self):
        """Should return all articles in the given year"""
        response = get_allowed(self.client, reverse('news-archive-year', kwargs={'year': 1999}))
        nose.tools.eq_(len(response.context['object_list']), 4)
        nose.tools.ok_(all(article.pub_date.year == 1999
                           for article in response.context['object_list']))

    def test_news_archive_month(self):
        """Should return all articel from the given month"""
        response = get_allowed(self.client,
                reverse('news-archive-month', kwargs={'year': 1999, 'month': 'jan'}))
        nose.tools.eq_(len(response.context['object_list']), 3)
        nose.tools.ok_(all(article.pub_date.year == 1999 and article.pub_date.month == 1
                           for article in response.context['object_list']))

    def test_news_archive_day(self):
        """Should return all article for the given day"""
        response = get_allowed(self.client,
                reverse('news-archive-day',
                    kwargs={'year': 1999, 'month': 'jan', 'day': 1}))
        nose.tools.eq_(len(response.context['object_list']), 2)
        nose.tools.ok_(all(article.pub_date.year == 1999 and article.pub_date.month == 1 and
                           article.pub_date.day == 1
                           for article in response.context['object_list']))

    def test_news_archive_day_empty(self):
        """Should return nothing for a day with no articles"""
        response = get_allowed(self.client,
                reverse('news-archive-day',
                    kwargs={'year': 1999, 'month': 'mar', 'day': 1}))
        nose.tools.eq_(len(response.context['object_list']), 0)

    def test_news_detail(self):
        """News detail should display the given article"""
        response = get_allowed(self.client,
                reverse('news-detail',
                    kwargs={
                        'year': 1999,
                        'month': 'jan',
                        'day': 1,
                        'slug': 'test-article-5'}))
        nose.tools.eq_(response.context['object'], Article.objects.get(slug='test-article-5'))

    def test_news_detail_404(self):
        """Should give a 404 error for a article that doesn't exist"""
        get_404(self.client, reverse('news-detail', kwargs={'year': 1999, 'month': 'mar',
                                                            'day': 1, 'slug': 'test-article-1'}))

    def test_feed(self):
        """Should have a feed"""
        get_allowed(self.client, reverse('news-feed'))

