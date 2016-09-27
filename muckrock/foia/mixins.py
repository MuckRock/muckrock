"""
Mixin callses that relate to FOIA requests
"""

from django.db.models import Avg, F, Sum

class RequestHelper(object):
    """Helper methods for classes that have a get_requests() method"""
    def average_response_time(self):
        """Get the average response time from a submitted to completed request"""
        requests = self.get_requests()
        avg = (requests.aggregate(avg=Avg(F('date_done') - F('date_submitted')))['avg'])
        return int(avg) if avg else 0

    def average_fee(self):
        """Get the average fees required on requests that have a price."""
        requests = self.get_requests()
        avg = requests.filter(price__gt=0).aggregate(price=Avg('price'))['price']
        return avg if avg else 0

    def fee_rate(self):
        """Get the percentage of requests that have a fee."""
        requests = self.get_requests()
        filed = float(requests.get_submitted().count())
        fee = float(requests.get_submitted().filter(price__gt=0).count())
        rate = 0
        if filed > 0:
            rate = fee/filed * 100
        return rate

    def success_rate(self):
        """Get the percentage of requests that are successful."""
        requests = self.get_requests()
        filed = float(requests.get_submitted().count())
        completed = float(requests.get_done().count())
        rate = 0
        if filed > 0:
            rate = completed/filed * 100
        return rate

    def total_pages(self):
        """Total pages released"""
        requests = self.get_requests()
        pages = requests.aggregate(Sum('files__pages'))['files__pages__sum']
        return pages if pages else 0
