"""
App config for accounts
"""

from django.apps import AppConfig, apps


class AccountsConfig(AppConfig):
    """Configures the accounts application to use activity streams"""
    name = 'muckrock.accounts'

    def ready(self):
        """Registers users with the activity streams plugin"""
        from actstream import registry
        from dashing.utils import router
        registry.register(apps.get_model('auth.User'))
        registry.register(self.get_model('Profile'))
        from muckrock.accounts.widgets import (
                ProcessingDaysWidget,
                ProcessingCountWidget,
                OldestProcessingWidget,
                ProcessingGraphWidget,
                FlagDaysWidget,
                FlagCountWidget,
                OldestFlagWidget,
                FlagGraphWidget,
                ProUserGraphWidget,
                RequestsFiledWidget,
                ProUserCountWidget,
                OrgUserCountWidget,
                RecentRequestsWidget,
                PageCountWidget,
                )
        router.register(ProcessingDaysWidget, 'processing_days_widget')
        router.register(ProcessingCountWidget, 'processing_count_widget')
        router.register(OldestProcessingWidget, 'oldest_processing_widget')
        router.register(ProcessingGraphWidget, 'processing_graph_widget')
        router.register(FlagDaysWidget, 'flag_days_widget')
        router.register(FlagCountWidget, 'flag_count_widget')
        router.register(OldestFlagWidget, 'oldest_flag_widget')
        router.register(FlagGraphWidget, 'flag_graph_widget')
        router.register(ProUserGraphWidget, 'pro_user_graph_widget')
        router.register(RequestsFiledWidget, 'requests_filed_widget')
        router.register(ProUserCountWidget, 'pro_user_count_widget')
        router.register(OrgUserCountWidget, 'org_user_count_widget')
        router.register(RecentRequestsWidget, 'recent_requests_widget')
        router.register(PageCountWidget, 'page_count_widget')
