"""
App config for jurisdiction
"""

# Django
from django.apps import AppConfig


class JurisdictionConfig(AppConfig):
    """Configures the jurisdiction application to use watson"""

    name = "muckrock.jurisdiction"

    def ready(self):
        """Registers exemptions with watson and imports signal handlers"""
        # pylint: disable=invalid-name, import-outside-toplevel
        # Third Party
        from watson import search

        Exemption = self.get_model("Exemption")
        search.register(Exemption)

        # Import signal handlers to register them
        from muckrock.jurisdiction import signals  # noqa: F401  # pylint: disable=unused-import
