"""
Tests using nose for the news application
"""

from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.test.client import Client
import nose.tools

from news.models import Article
from muckrock.tests import get_allowed, get_404

def setup():
    """Clean the database before each test"""
    User.objects.all().delete()
    Article.objects.all().delete()

 # models
@nose.tools.with_setup(setup)
def test_article_model_unicode():
    """Test the Article model's __unicode__ method"""
    user = User.objects.create(username='Test_User')
    article = Article.objects.create(title='Test Article', author=user)
    nose.tools.eq_(unicode(article), u'Test Article')

@nose.tools.with_setup(setup)
def test_article_model_url():
    """Test the Article model's get_absolute_url method"""
    user = User.objects.create(username='Test_User')
    article = Article.objects.create(title='Test Article', author=user,
                                     pub_date=datetime(1984, 12, 29), slug='test-article')
    nose.tools.eq_(article.get_absolute_url(), '/news/archives/1984/dec/29/test-article/')

 # manager
@nose.tools.with_setup(setup)
def test_manager_get_published():
    """Test the Article Manager's get_punlished method"""
    tomorrow = datetime.now() + timedelta(1)
    user = User.objects.create(username='Test_User')

    article1 = Article.objects.create(title='Test Article 1', pub_date=datetime(1984, 12, 29),
                                     author=user, slug='test-article-1', publish=True)
    Article.objects.create(title='Test Article 2', pub_date=datetime(1989, 12, 29),
                          author=user, slug='test-article-2', publish=False)
    Article.objects.create(title='Test Article 3', pub_date=tomorrow,
                          author=user, slug='test-article-3', publish=True)
    Article.objects.create(title='Test Article 4', pub_date=tomorrow,
                          author=user, slug='test-article-4', publish=False)
    article5 = Article.objects.create(title='Test Article 5', pub_date=datetime(1999, 1, 1),
                                     author=user, slug='test-article-5', publish=True)

    nose.tools.eq_(set(Article.objects.get_published()), set([article1, article5]))

@nose.tools.with_setup(setup)
def test_manager_get_drafts():
    """Test the Article Manager's get_drafts method"""
    tomorrow = datetime.now() + timedelta(1)
    user = User.objects.create(username='Test_User')

    Article.objects.create(title='Test Article 1', pub_date=datetime(1984, 12, 29),
                          author=user, slug='test-article-1', publish=True)
    article2 = Article.objects.create(title='Test Article 2', pub_date=datetime(1989, 12, 29),
                                     author=user, slug='test-article-2', publish=False)
    Article.objects.create(title='Test Article 3', pub_date=tomorrow,
                          author=user, slug='test-article-3', publish=True)
    article4 = Article.objects.create(title='Test Article 4', pub_date=tomorrow,
                                     author=user, slug='test-article-4', publish=False)
    Article.objects.create(title='Test Article 5', pub_date=datetime(1999, 1, 1),
                          author=user, slug='test-article-5', publish=True)

    nose.tools.eq_(set(Article.objects.get_drafts()), set([article2, article4]))

 # views
@nose.tools.with_setup(setup)
def test_views():
    """Test views"""

    client = Client()
    tomorrow = datetime.now() + timedelta(1)
    user = User.objects.create(username='Test_User')

    Article.objects.create(title='Test Article 1', pub_date=datetime(1984, 12, 29),
                          author=user, slug='test-article-1', publish=True)
    Article.objects.create(title='Test Article 2', pub_date=datetime(1989, 12, 29),
                          author=user, slug='test-article-2', publish=False)
    Article.objects.create(title='Test Article 3', pub_date=tomorrow,
                          author=user, slug='test-article-3', publish=True)
    Article.objects.create(title='Test Article 4', pub_date=tomorrow,
                          author=user, slug='test-article-4', publish=False)
    article5 = Article.objects.create(title='Test Article 5', pub_date=datetime(1999, 1, 1),
                                      author=user, slug='test-article-5', publish=True)
    Article.objects.create(title='Test Article 6', pub_date=datetime(1999, 1, 1),
                          author=user, slug='test-article-6', publish=True)
    Article.objects.create(title='Test Article 7', pub_date=datetime(1999, 1, 2),
                          author=user, slug='test-article-7', publish=True)
    Article.objects.create(title='Test Article 8', pub_date=datetime(1999, 2, 2),
                          author=user, slug='test-article-8', publish=True)

    response = get_allowed(client, '/news/', ['news/article_archive.html', 'news/base.html'])
    nose.tools.eq_(len(response.context['latest']), 5)

    response = get_allowed(client, '/news/archives/1999/',
                           ['news/article_archive_year.html', 'news/base.html'])
    nose.tools.eq_(len(response.context['object_list']), 4)
    nose.tools.ok_(all(article.pub_date.year == 1999
                       for article in response.context['object_list']))

    response = get_allowed(client, '/news/archives/1999/jan/',
                           ['news/article_archive_month.html', 'news/base.html'])
    nose.tools.eq_(len(response.context['object_list']), 3)
    nose.tools.ok_(all(article.pub_date.year == 1999 and article.pub_date.month == 1
                       for article in response.context['object_list']))

    response = get_allowed(client, '/news/archives/1999/jan/1/',
                           ['news/article_archive_day.html', 'news/base.html'])
    nose.tools.eq_(len(response.context['object_list']), 2)
    nose.tools.ok_(all(article.pub_date.year == 1999 and article.pub_date.month == 1 and
                       article.pub_date.day == 1
                       for article in response.context['object_list']))

    response = get_allowed(client, '/news/archives/1999/jan/1/test-article-5/',
                           ['news/article_detail.html', 'news/base.html'])
    nose.tools.eq_(response.context['object'], article5)

    response = get_allowed(client, '/news/archives/1999/mar/1/',
                           ['news/article_archive_day.html', 'news/base.html'])
    nose.tools.eq_(len(response.context['object_list']), 0)

    get_404(client, '/news/1999/mar/1/test-article-1/')
