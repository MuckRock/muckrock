"""
App config for tasks
"""

from django.apps import AppConfig


class TaskConfig(AppConfig):
    """Configures PDF generation for snail mail tasks"""
    name = 'muckrock.task'

    def ready(self):
        """Sets global options for FPDF"""
        from fpdf import set_global
        from tempfile import mkdtemp
        # cache in a temp directory since the font
        # directory is read only on heroku
        set_global('FPDF_CACHE_MODE', 2)
        set_global('FPDF_CACHE_DIR', mkdtemp())
