# -*- coding: utf-8 -*-
"""
App loader for core app
"""

# Django
from django.apps import AppConfig, apps
from django.conf import settings


class CoreConfig(AppConfig):
    """App config for core app"""

    name = "muckrock.core"

    def ready(self):
        """Register flatpages with Watson"""
        # pylint: disable=invalid-name, import-outside-toplevel
        # Third Party
        from watson import search

        FlatPage = apps.get_model("flatpages", "FlatPage")

        if "//" in settings.MUCKROCK_URL:
            domain = settings.MUCKROCK_URL.split("//", 1)[1]
        else:
            domain = ""
        search.register(FlatPage.objects.filter(sites__domain=domain))
