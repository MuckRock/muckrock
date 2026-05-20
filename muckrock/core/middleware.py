# Django
from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.utils.deprecation import MiddlewareMixin

# Standard Library
import logging

logger = logging.getLogger("http_requests")


class FlatpageRedirectMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if response.status_code == 404:
            site = request.get_host()
            path = request.path_info.lstrip("/")
            redirects = getattr(settings, "FLATPAGES_REDIRECTS", {})
            if site in redirects:
                site_redirects = redirects[site]
                if path in site_redirects:
                    return HttpResponsePermanentRedirect(site_redirects[path])
        return response


class LogHTTPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        logger.info(
            "%s %s",
            request.method,
            request.path,
            extra={
                "request": self.format_request(request),
                "response": self.format_response(response),
            },
        )

        return response

    def format_request(self, request):
        """Format a request for logging"""
        return {
            "user": self.format_user(request.user),
            "path": request.path,
            "method": request.method,
            "headers": dict(request.headers),
            "get": dict(request.GET),
            "body": request.body.decode("utf-8"),
        }

    def format_user(self, user):
        """Format a user for logging"""
        if user.is_authenticated:
            return {
                "id": user.pk,
                "username": user.username,
                "email": user.email,
                "full_name": user.profile.full_name,
                "verified_journalist": user.profile.verified_journalist,
                "organization": self.format_organization(user.profile.organization),
            }
        return None

    def format_organization(self, org):
        """Format an organization for logging"""
        return {
            "id": org.pk,
            "name": org.name,
            "individual": org.individual,
            "verified_journalist": org.verified_journalist,
            "entitlement": org.entitlement.slug if org.entitlement_id else None,
            "monthly_requests": org.monthly_requests,
            "number_requests": org.number_requests,
        }

    def format_response(self, response):
        """Format a response for logging"""
        return {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.content.decode("utf-8")[:2000],
        }
