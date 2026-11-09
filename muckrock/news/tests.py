"""
Tests for the news application
"""

# Django
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

# Standard Library
import xml.etree.ElementTree as ET
from datetime import datetime

# Third Party
import pytz
from freezegun import freeze_time

# MuckRock
from muckrock.core.factories import ArticleFactory, ProjectFactory, UserFactory
from muckrock.core.helpers import get_404, get_allowed
from muckrock.core.test_utils import mock_middleware
from muckrock.news.models import Article
from muckrock.news.views import NewsDetail
from muckrock.project.forms import ProjectManagerForm


class TestNewsUnit(TestCase):
    """Unit tests for news"""

    def setUp(self):
        """Set up tests"""
        self.article = ArticleFactory()

    # models
    def test_article_model_str(self):
        """Test the Article model's __str__ method"""
        assert str(self.article)

    def test_article_model_url(self):
        """Test the Article model's get_absolute_url method"""
        pub_date = timezone.localtime(self.article.pub_date)
        assert self.article.get_absolute_url() == reverse(
            "news-detail",
            kwargs={
                "year": pub_date.strftime("%Y"),
                "month": pub_date.strftime("%b").lower(),
                "day": pub_date.strftime("%d"),
                "slug": self.article.slug,
            },
        )

    # manager
    def test_manager_get_published(self):
        """Test the Article Manager's get_published method"""
        article1 = ArticleFactory(publish=True)
        article2 = ArticleFactory(publish=True)
        published = Article.objects.get_published()
        assert article1 in published and article2 in published
        assert all(a.publish and a.pub_date <= timezone.now() for a in published)
        assert published.count() == 2

    def test_manager_get_drafts(self):
        """Test the Article Manager's get_drafts method"""
        drafted = Article.objects.get_drafts()
        assert self.article in drafted
        assert all(not a.publish for a in drafted)
        assert drafted.count() == 1


class TestNewsFunctional(TestCase):
    """Functional tests for news"""

    def setUp(self):
        """Create articles for the tests"""
        ArticleFactory.create_batch(
            2, publish=True, pub_date=datetime(1999, 1, 1, 12, 12, tzinfo=pytz.utc)
        )
        ArticleFactory(publish=True, pub_date=datetime(1999, 1, 2, 12, tzinfo=pytz.utc))
        ArticleFactory(publish=True, pub_date=datetime(1999, 2, 3, 12, tzinfo=pytz.utc))
        ArticleFactory(publish=True, pub_date=datetime(2000, 6, 6, tzinfo=pytz.utc))

    # views
    def test_news_index(self):
        """Should redirect to list"""
        get_allowed(self.client, reverse("news-index"))

    def test_news_archive(self):
        """Should return all articles"""
        response = get_allowed(self.client, reverse("news-archive"))
        assert len(response.context["object_list"]) == 5

    def test_news_archive_year(self):
        """Should return all articles in the given year"""
        response = get_allowed(
            self.client, reverse("news-archive-year", kwargs={"year": 1999})
        )
        assert len(response.context["object_list"]) == 4
        assert all(
            article.pub_date.year == 1999 for article in response.context["object_list"]
        )

    def test_news_archive_month(self):
        """Should return all articel from the given month"""
        response = get_allowed(
            self.client,
            reverse("news-archive-month", kwargs={"year": 1999, "month": "jan"}),
        )
        assert len(response.context["object_list"]) == 3
        assert all(
            article.pub_date.year == 1999 and article.pub_date.month == 1
            for article in response.context["object_list"]
        )

    def test_news_archive_day(self):
        """Should return all article for the given day"""
        response = get_allowed(
            self.client,
            reverse(
                "news-archive-day", kwargs={"year": 1999, "month": "jan", "day": 1}
            ),
        )
        assert len(response.context["object_list"]) == 2
        assert all(
            article.pub_date.year == 1999
            and article.pub_date.month == 1
            and article.pub_date.day == 1
            for article in response.context["object_list"]
        )

    def test_news_archive_day_empty(self):
        """Should return 404 for a day with no articles"""
        get_404(
            self.client,
            reverse(
                "news-archive-day", kwargs={"year": 1999, "month": "mar", "day": 1}
            ),
        )

    def test_news_detail(self):
        """News detail should display the given article"""
        article = ArticleFactory(
            publish=True, pub_date=datetime(1999, 1, 1, 12, tzinfo=pytz.utc)
        )
        response = get_allowed(
            self.client,
            reverse(
                "news-detail",
                kwargs={"year": 1999, "month": "jan", "day": 1, "slug": article.slug},
            ),
        )
        assert response.context["object"] == article

    def test_news_detail_404(self):
        """Should give a 404 error for a article that doesn't exist"""
        get_404(
            self.client,
            reverse(
                "news-detail",
                kwargs={
                    "year": 1999,
                    "month": "mar",
                    "day": 1,
                    "slug": "test-article-1",
                },
            ),
        )

    def test_feed(self):
        """Should have a feed"""
        get_allowed(self.client, reverse("news-feed"))


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
        pub_date = timezone.localtime(self.article.pub_date)
        return self.view(
            request,
            slug=self.article.slug,
            year=pub_date.strftime("%Y"),
            month=pub_date.strftime("%b").lower(),
            day=pub_date.strftime("%d"),
        )

    def test_set_tags(self):
        """Posting a group of tags to an article should set the tags on that article."""
        tags = ["foo", "bar", "baz"]
        staff = UserFactory(is_staff=True)
        response = self.post_helper({"tags": tags}, staff)
        self.article.refresh_from_db()
        assert response.status_code, 200
        assert "foo" in [tag.name for tag in self.article.tags.all()]
        assert "bar" in [tag.name for tag in self.article.tags.all()]
        assert "baz" in [tag.name for tag in self.article.tags.all()]

    def test_set_projects(self):
        """Posting a group of projects to an article should set that article's
        projects."""
        project1 = ProjectFactory()
        project2 = ProjectFactory()
        staff = UserFactory(is_staff=True)
        project_form = ProjectManagerForm(
            {"projects": [project1.pk, project2.pk]}, user=staff
        )
        assert project_form.is_valid(), "We want to be sure we are posting valid data."
        data = {"action": "projects"}
        data.update(project_form.data)
        response = self.post_helper(data, staff)
        self.article.refresh_from_db()
        project1.refresh_from_db()
        project2.refresh_from_db()
        assert response.status_code, 200
        assert (
            self.article in project1.articles.all()
        ), "The article should be added to the project."
        assert (
            self.article in project2.articles.all()
        ), "The article should be added to teh project."

    def test_staff_only(self):
        """Non-staff users cannot edit articles."""
        user = UserFactory()
        response = self.post_helper({"tags": "hello"}, user)
        assert (
            response.status_code == 403
        ), "The server should return a 403 Forbidden error code."


@freeze_time("2026-11-05 12:00:00")
class TestNewsSitemap(TestCase):
    """Google News sitemap"""

    ns = {
        "s": "http://www.sitemaps.org/schemas/sitemap/0.9",
        "news": "http://www.google.com/schemas/sitemap-news/0.9",
    }

    def setUp(self):
        self.recent = ArticleFactory(
            title="Courts & <Cops>",
            publish=True,
            pub_date=datetime(2026, 11, 4, 14, 30, 15, 123456, tzinfo=pytz.utc),
        )
        ArticleFactory(publish=True, pub_date=datetime(2026, 11, 1, tzinfo=pytz.utc))
        ArticleFactory(publish=False, pub_date=datetime(2026, 11, 4, tzinfo=pytz.utc))

    def test_lists_only_articles_published_in_the_last_two_days(self):
        response = self.client.get("/news-sitemaps/articles.xml")

        assert response.status_code == 200
        urls = ET.fromstring(response.content).findall("s:url", self.ns)
        assert [u.find("s:loc", self.ns).text for u in urls] == [
            "http://example.com" + self.recent.get_absolute_url()
        ]
        news = urls[0].find("news:news", self.ns)
        assert news.find("news:title", self.ns).text == "Courts & <Cops>"
        assert news.find("news:publication/news:name", self.ns).text == "MuckRock"
        assert news.find("news:publication/news:language", self.ns).text == "en"
        assert (
            news.find("news:publication_date", self.ns).text
            == "2026-11-04T09:30:15-05:00"
        )

    def test_index_links_to_the_articles_sitemap(self):
        response = self.client.get("/news-sitemaps/index.xml")

        assert response.status_code == 200
        locs = ET.fromstring(response.content).findall("s:sitemap/s:loc", self.ns)
        assert [loc.text for loc in locs] == [
            "http://example.com/news-sitemaps/articles.xml"
        ]

    def test_unknown_section_is_not_found(self):
        response = self.client.get("/news-sitemaps/nope.xml")

        assert response.status_code == 404
