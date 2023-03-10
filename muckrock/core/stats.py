"""
Utilities for calculating stats for agencies and jurisdictions
"""

# Django
from django.db.models import Count

def collect_stats(obj, context):
    """Helper for collecting stats"""
    statuses = ("rejected", "ack", "processed", "fix", "no_docs", "done", "appealing")
    requests = obj.get_requests()
    status_counts = (
        requests.filter(status__in=statuses)
        .order_by("status")
        .values_list("status")
        .annotate(Count("status"))
    )
    context.update({"num_%s" % s: c for s, c in status_counts})
    context["num_overdue"] = requests.get_overdue().count()
    context["num_submitted"] = requests.count()