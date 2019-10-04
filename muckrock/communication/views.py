"""
Views for the communication app
"""

# Django
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.db.models.aggregates import Sum
from django.db.models.query import Prefetch
from django.views.generic.detail import DetailView

# MuckRock
from muckrock.communication.filters import CheckFilterSet
from muckrock.communication.models import (
    Check,
    EmailAddress,
    EmailCommunication,
    EmailError,
    EmailOpen,
    FaxCommunication,
    FaxError,
    PhoneNumber,
)
from muckrock.core.views import MRFilterListView, class_view_decorator


class EmailDetailView(DetailView):
    """Show message open and error detail for an email address"""
    _prefetch_queryset = (
        EmailCommunication.objects.select_related(
            'communication__foia__agency__jurisdiction',
            'from_email',
        ).prefetch_related(
            Prefetch(
                'opens',
                queryset=EmailOpen.objects.select_related('recipient'),
            ),
            Prefetch(
                'errors',
                queryset=EmailError.objects.select_related('recipient'),
            ),
            'to_emails',
            'cc_emails',
        )
    )
    queryset = EmailAddress.objects.prefetch_related(
        Prefetch('from_emails', queryset=_prefetch_queryset),
        Prefetch('to_emails', queryset=_prefetch_queryset),
        Prefetch('cc_emails', queryset=_prefetch_queryset),
    )
    template_name = 'communication/email_detail.html'
    pk_url_kwarg = 'idx'
    context_object_name = 'email_address'

    def get_context_data(self, **kwargs):
        """Add all email messages"""
        context = super(EmailDetailView, self).get_context_data(**kwargs)
        email_address = self.object
        context['emails'] = email_address.from_emails.union(
            email_address.to_emails.all(),
            email_address.cc_emails.all(),
        ).order_by('sent_datetime')
        context['sidebar_admin_url'] = reverse(
            'admin:communication_emailaddress_change', args=(email_address.pk,)
        )
        return context


class PhoneDetailView(DetailView):
    """Show message error detail for a fax number"""
    _prefetch_queryset = (
        FaxCommunication.objects.select_related(
            'communication__foia__agency__jurisdiction',
            'to_number',
        ).prefetch_related(
            Prefetch(
                'errors',
                queryset=FaxError.objects.select_related('recipient'),
            ),
        )
    )
    queryset = PhoneNumber.objects.prefetch_related(
        Prefetch('faxes', queryset=_prefetch_queryset),
    )
    template_name = 'communication/fax_detail.html'
    pk_url_kwarg = 'idx'
    context_object_name = 'phone_number'

    def get_context_data(self, **kwargs):
        """Add all email messages"""
        context = super(PhoneDetailView, self).get_context_data(**kwargs)
        phone_number = self.object
        context['faxes'] = phone_number.faxes.order_by('sent_datetime')
        context['sidebar_admin_url'] = reverse(
            'admin:communication_phonenumber_change', args=(phone_number.pk,)
        )
        return context


@class_view_decorator(user_passes_test(lambda u: u.is_staff))
class CheckListView(MRFilterListView):
    """List of all checks we have issued"""
    model = Check
    title = 'Checks'
    template_name = 'communication/check_list.html'
    filter_class = CheckFilterSet
    queryset = Check.objects.select_related(
        'agency__jurisdiction', 'communication__foia', 'user'
    )

    def get_context_data(self, **kwargs):
        context = super(CheckListView, self).get_context_data(**kwargs)
        context['outstanding'] = Check.objects.filter(
            deposit_time=None
        ).aggregate(total=Sum('amount'))['total']
        return context
