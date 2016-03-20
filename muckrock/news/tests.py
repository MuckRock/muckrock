"""
Tests using nose for the news application
"""

from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory

from nose.tools import eq_, ok_
from datetime import datetime

from muckrock.factories import ArticleFactory, UserFactory, ProjectFactory
from muckrock.news.models import Article
from muckrock.news.views import NewsDetail
from muckrock.project.forms import ProjectManagerForm
from muckrock.tests import get_allowed, get_404
from muckrock.utils import mock_middleware

# pylint: disable=no-self-use
# pylint: disable=too-many-public-methods

class TestNewsUnit(TestCase):
    """Unit tests for news"""

    def setUp(self):
        """Set up tests"""
        self.article = ArticleFactory()

    # models
    def test_article_model_unicode(self):
        """Test the Article model's __unicode__ method"""
        ok_(unicode(self.article))

    def test_article_model_url(self):
        """Test the Article model's get_absolute_url method"""
        eq_(self.article.get_absolute_url(), reverse('news-detail', kwargs={
            'year': self.article.pub_date.year,
            'month': self.article.pub_date.strftime('%b').lower(),
            'day': self.article.pub_date.day,
            'slug': self.article.slug
        }))

    # manager
    def test_manager_get_published(self):
        """Test the Article Manager's get_published method"""
        # pylint: disable=no-self-use
        article1 = ArticleFactory(publish=True)
        article2 = ArticleFactory(publish=True)
        published = Article.objects.get_published()
        ok_(article1 in published and article2 in published)
        ok_(all(a.publish and a.pub_date <= datetime.now() for a in published))
        eq_(published.count(), 2)

    def test_manager_get_drafts(self):
        """Test the Article Manager's get_drafts method"""
        drafted = Article.objects.get_drafts()
        ok_(self.article in drafted)
        ok_(all(not a.publish for a in drafted))
        eq_(drafted.count(), 1)


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
        eq_(len(response.context['object_list']), 4)
        ok_(all(article.pub_date.year == 1999
                           for article in response.context['object_list']))

    def test_news_archive_month(self):
        """Should return all articel from the given month"""
        response = get_allowed(self.client,
                reverse('news-archive-month', kwargs={'year': 1999, 'month': 'jan'}))
        eq_(len(response.context['object_list']), 3)
        ok_(all(article.pub_date.year == 1999 and article.pub_date.month == 1
                           for article in response.context['object_list']))

    def test_news_archive_day(self):
        """Should return all article for the given day"""
        response = get_allowed(self.client,
                reverse('news-archive-day',
                    kwargs={'year': 1999, 'month': 'jan', 'day': 1}))
        eq_(len(response.context['object_list']), 2)
        ok_(all(article.pub_date.year == 1999 and article.pub_date.month == 1 and
                           article.pub_date.day == 1
                           for article in response.context['object_list']))

    def test_news_archive_day_empty(self):
        """Should return nothing for a day with no articles"""
        response = get_allowed(self.client,
                reverse('news-archive-day',
                    kwargs={'year': 1999, 'month': 'mar', 'day': 1}))
        eq_(len(response.context['object_list']), 0)

    def test_news_detail(self):
        """News detail should display the given article"""
        response = get_allowed(self.client,
                reverse('news-detail',
                    kwargs={
                        'year': 1999,
                        'month': 'jan',
                        'day': 1,
                        'slug': 'test-article-5'}))
        eq_(response.context['object'], Article.objects.get(slug='test-article-5'))

    def test_news_detail_404(self):
        """Should give a 404 error for a article that doesn't exist"""
        get_404(self.client, reverse('news-detail', kwargs={'year': 1999, 'month': 'mar',
                                                            'day': 1, 'slug': 'test-article-1'}))

    def test_feed(self):
        """Should have a feed"""
        get_allowed(self.client, reverse('news-feed'))


class TestNewsArticleViews(TestCase):
    """Tests the functions attached to news article views"""
    def setUp(self):
        self.article = ArticleFactory(publish=True)
        self.request_factory = RequestFactory()
        self.url = self.article.get_absolute_url()
        self.view = NewsDetail.as_view()

    def post_helper(self, data, user):
        """Returns a post response"""
        request = self.request_factory.post(self.url, data)
        request.user = user
        request = mock_middleware(request)
        return self.view(
            request,
            slug=self.article.slug,
            year=self.article.pub_date.strftime('%Y'),
            month=self.article.pub_date.strftime('%b').lower(),
            day=self.article.pub_date.strftime('%d')
        )

    def test_set_tags(self):
        """Posting a group of tags to an article should set the tags on that article."""
        tags = "foo, bar, baz"
        staff = UserFactory(is_staff=True)
        response = self.post_helper({'tags': tags}, staff)
        self.article.refresh_from_db()
        ok_(response.status_code, 200)
        ok_('foo' in [tag.name for tag in self.article.tags.all()])
        ok_('bar' in [tag.name for tag in self.article.tags.all()])
        ok_('baz' in [tag.name for tag in self.article.tags.all()])

    def test_set_projects(self):
        """Posting a group of projects to an article should set that article's projects."""
        project1 = ProjectFactory()
        project2 = ProjectFactory()
        project_form = ProjectManagerForm({'projects': [project1.pk, project2.pk]})
        ok_(project_form.is_valid(),
            'We want to be sure we are posting valid data.')
        staff = UserFactory(is_staff=True)
        data = {'action': 'projects'}
        data.update(project_form.data)
        response = self.post_helper(data, staff)
        self.article.refresh_from_db()
        project1.refresh_from_db()
        project2.refresh_from_db()
        ok_(response.status_code, 200)
        ok_(self.article in project1.articles.all(),
            'The article should be added to the project.')
        ok_(self.article in project2.articles.all(),
            'The article should be added to teh project.')

    def test_staff_only(self):
        """Non-staff users cannot edit articles."""
        user = UserFactory()
        response = self.post_helper({'tags': 'hello'}, user)
        eq_(response.status_code, 403,
            'The server should return a 403 Forbidden error code.')
