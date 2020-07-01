"""Tasks for the communication app"""

# Django
from celery.schedules import crontab
from celery.task import periodic_task
from django.conf import settings

# Standard Library
import logging
import re
import sys
from datetime import date, datetime, timedelta

# Third Party
import plaid
from numpy import isclose

# MuckRock
from muckrock.communication.models import Check

logger = logging.getLogger(__name__)


@periodic_task(
    run_every=crontab(hour=1, minute=30),
    name='muckrock.communication.tasks.plaid_checks',
)
def plaid_checks():
    """Get transaction information from Plaid to record deposited checks"""
    client = plaid.Client(
        client_id=settings.PLAID_CLIENT_ID,
        secret=settings.PLAID_SECRET,
        public_key=settings.PLAID_PUBLIC_KEY,
        environment=settings.PLAID_ENV,
        api_version='2019-05-29'
    )
    start_date = str(date.today() - timedelta(14))
    end_date = str(date.today())
    try:
        transactions_response = client.Transactions.get(
            settings.PLAID_ACCESS_TOKEN, start_date, end_date
        )
    except plaid.errors.PlaidError as exc:
        logger.error(exc, exc_info=sys.exc_info())

    p_check_number = re.compile(r'^Check ([0-9]+)$')
    for transaction in transactions_response['transactions']:
        m_check_number = p_check_number.match(transaction['name'])
        if m_check_number:
            check_number = m_check_number.group(1)
            deposit_date = datetime.strptime(transaction['date'], '%Y-%m-%d')
            amount = transaction['amount']
            try:
                check = Check.objects.get(number=check_number)
            except Check.DoesNotExist:
                logger.warning("Check #%s does not exist", check_number)
                continue
            if check.deposit_date:
                continue

            if not isclose(amount, float(check.amount)):
                logger.error(
                    "Check #%s amount does not match: %s, %s",
                    check_number,
                    amount,
                    check.amount,
                )

            check.deposit_date = deposit_date
            check.save()
