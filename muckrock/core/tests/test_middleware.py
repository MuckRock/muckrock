# Django
from django.http import HttpResponse, HttpResponseNotFound
from django.test import RequestFactory, TestCase, override_settings

# MuckRock
from muckrock.core.middleware import FlatpageRedirectMiddleware


class FlatpageRedirectMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = FlatpageRedirectMiddleware(lambda request: HttpResponse())

    @override_settings(
        ALLOWED_HOSTS=[
            "www.muckrock.com",
            "www.foiamachine.org",
            "www.unknownsite.org",
        ],
        FLATPAGES_REDIRECTS={
            "www.muckrock.com": {
                "about/how-we-work/": "https://help.muckrock.com/how-we-work-redirect",
            },
            "www.foiamachine.org": {
                "about/": "https://help.muckrock.com/foia-about-redirect",
            },
        },
    )
    def test_redirect_muckrock_domain(self):
        # Request for a known route in the mocks above
        request = self.factory.get("/about/how-we-work/")
        request.META["HTTP_HOST"] = "www.muckrock.com"
        response = HttpResponseNotFound()
        redirected = self.middleware.process_response(request, response)
        self.assertEqual(redirected.status_code, 301)
        self.assertEqual(
            redirected.url, "https://help.muckrock.com/how-we-work-redirect"
        )

    @override_settings(
        ALLOWED_HOSTS=[
            "www.muckrock.com",
            "www.foiamachine.org",
            "www.unknownsite.org",
        ],
        FLATPAGES_REDIRECTS={
            "www.muckrock.com": {
                "about/how-we-work/": "https://help.muckrock.com/how-we-work-redirect",
            },
            "www.foiamachine.org": {
                "about/": "https://help.muckrock.com/foia-about-redirect",
            },
        },
    )
    def test_redirect_foiamachine_domain(self):
        request = self.factory.get("/about/")
        request.META["HTTP_HOST"] = "www.foiamachine.org"
        response = HttpResponseNotFound()
        redirected = self.middleware.process_response(request, response)
        self.assertEqual(redirected.status_code, 301)
        self.assertEqual(
            redirected.url, "https://help.muckrock.com/foia-about-redirect"
        )

    @override_settings(
        ALLOWED_HOSTS=[
            "www.muckrock.com",
            "www.foiamachine.org",
            "www.unknownsite.org",
        ],
        FLATPAGES_REDIRECTS={
            "www.muckrock.com": {
                "about/how-we-work/": "https://help.muckrock.com/how-we-work-redirect",
            }
        },
    )
    def test_no_redirect_unknown_site(self):
        request = self.factory.get("/about/how-we-work/")
        request.META["HTTP_HOST"] = "www.unknownsite.org"
        response = HttpResponseNotFound()
        new_response = self.middleware.process_response(request, response)
        self.assertEqual(new_response.status_code, 404)

    @override_settings(
        ALLOWED_HOSTS=[
            "www.muckrock.com",
            "www.foiamachine.org",
            "www.unknownsite.org",
        ],
        FLATPAGES_REDIRECTS={
            "www.muckrock.com": {
                "about/how-we-work/": "https://help.muckrock.com/how-we-work-redirect",
            }
        },
    )
    def test_no_redirect_unknown_path(self):
        request = self.factory.get("/unknown/path/")
        request.META["HTTP_HOST"] = "www.muckrock.com"
        response = HttpResponseNotFound()
        new_response = self.middleware.process_response(request, response)
        self.assertEqual(new_response.status_code, 404)

    def test_returns_original_response_if_not_404(self):
        request = self.factory.get("/")
        request.META["HTTP_HOST"] = "www.muckrock.com"
        response = HttpResponse(status=200)
        new_response = self.middleware.process_response(request, response)
        self.assertEqual(new_response.status_code, 200)
