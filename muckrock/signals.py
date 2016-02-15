"""
Signal processor for plugins
"""

from celery_haystack.signals import CelerySignalProcessor

class RelatedCelerySignalProcessor(CelerySignalProcessor):
    """Update the index in real time using celery"""

    def handle_save(self, sender, instance, **kwargs):
        if hasattr(instance, 'reindex_related'):
            for related in instance.reindex_related:
                related_obj = getattr(instance, related)
                self.handle_save(related_obj.__class__, related_obj)
        return super(RelatedCelerySignalProcessor, self).handle_save(sender, instance, **kwargs)

    def handle_delete(self, sender, instance, **kwargs):
        if hasattr(instance, 'reindex_related'):
            for related in instance.reindex_related:
                related_obj = getattr(instance, related)
                self.handle_delete(related_obj.__class__, related_obj)
        return super(RelatedCelerySignalProcessor, self).handle_delete(sender, instance, **kwargs)
