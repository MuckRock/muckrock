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


def assign_grade(grade, text, percentile=None):
    if percentile:
        text = text.format(round(percentile, 2))
    return {"grade": grade, "text": text}


def grade_agency(agency, context):
    """Score the agency based on relative stats"""
    context["grades"] = {
        "abs_response_time": grade_absolute_response_time(agency),
        "rel_response_time": grade_relative_response_time(agency),
        "success_rate": grade_success_rate(agency),
        "fee_rate": grade_fee_rate(agency),
        "fee_average": grade_fee_average(agency),
    }


def grade_absolute_response_time(agency):
    """Do they respond within the legally allowed time?"""
    if not agency.jurisdiction.days:
        return assign_grade(
            "neutral", "The agency's jurisdiction has no mandated response time."
        )
    if agency.jurisdiction.days >= agency.average_response_time():
        return assign_grade(
            "pass", "On average, they respond within the legally allowed time."
        )
    else:
        return assign_grade(
            "fail", "On average, they take longer to respond than allowed by law."
        )


def grade_relative_response_time(agency):
    """Do they respond faster than other agencies in the jurisdiction?"""
    agency_average_response_time = agency.average_response_time()
    jurisdiction_average_response_time = agency.jurisdiction.average_response_time()
    if (
        agency.jurisdiction.agencies.count() < 2
        or agency_average_response_time == 0
        or jurisdiction_average_response_time == 0
    ):
        return assign_grade("neutral", "Not enough data available to evaluate agency")
    elif agency_average_response_time <= jurisdiction_average_response_time:
        percentile = (
            1 - (agency_average_response_time / jurisdiction_average_response_time)
        ) * 100
        return assign_grade(
            "pass",
            """They typically respond {}% faster than
            other agencies in their jurisdiction""",
            percentile,
        )
    else:
        percentile = (
            (agency_average_response_time / jurisdiction_average_response_time) - 1
        ) * 100
        return assign_grade(
            "fail",
            """They typically respond {}% slower than
            other agencies in their jurisdiction""",
            percentile,
        )


def grade_success_rate(agency):
    """Do they fulfill requests more than other agencies in the jurisdiction?"""
    agency_success_rate = agency.success_rate()
    jurisdiction_success_rate = agency.jurisdiction.success_rate()
    if (
        agency.jurisdiction.agencies.count() < 2
        or jurisdiction_success_rate == 0
        or agency_success_rate == 0
    ):
        return assign_grade("neutral", "Not enough data available to evaluate agency")
    elif agency_success_rate >= jurisdiction_success_rate:
        percentile = ((agency_success_rate / jurisdiction_success_rate) - 1) * 100
        return assign_grade(
            "pass",
            """They fulfill {}% more requests than
            other agencies in their jurisdiction.""",
            percentile,
        )
    else:
        percentile = (1 - (agency_success_rate / jurisdiction_success_rate)) * 100
        return assign_grade(
            "fail",
            """They fulfill {}% fewer requests than
            other agencies in their jurisdiction.""",
            percentile,
        )


def grade_fee_rate(agency):
    """Do they charge feeds more often than other agencies in the jurisdiction?"""
    agency_fee_rate = agency.fee_rate()
    jurisdiction_fee_rate = agency.jurisdiction.fee_rate()
    if (
        agency.jurisdiction.agencies.count() < 2
        or agency_fee_rate == 0
        or jurisdiction_fee_rate == 0
    ):
        return assign_grade("neutral", "Not enough data available to evaluate agency")
    elif agency_fee_rate <= jurisdiction_fee_rate:
        percentile = (1 - (agency_fee_rate / jurisdiction_fee_rate)) * 100
        return assign_grade(
            "pass",
            """They require a fee {}% less often than
            other agencies in their jurisdiction.""",
            percentile,
        )
    else:
        percentile = ((agency_fee_rate / jurisdiction_fee_rate) - 1) * 100
        return assign_grade(
            "fail",
            """They require a fee {}% more often than
            other agencies in their jurisdiction.""",
            percentile,
        )


def grade_fee_average(agency):
    """Do they charge feeds higher than other agencies in the jurisdiction?"""
    agency_fee_average = agency.average_fee()
    jurisdiction_fee_average = agency.jurisdiction.average_fee()
    if (
        agency.jurisdiction.agencies.count() < 2
        or agency_fee_average == 0
        or jurisdiction_fee_average == 0
    ):
        return assign_grade("neutral", "Not enough data available to evaluate agency")
    elif agency_fee_average <= jurisdiction_fee_average:
        percentile = (1 - (agency_fee_average / jurisdiction_fee_average)) * 100
        return assign_grade(
            "pass",
            """On average, they charge {}% lower fees
            than other agencies in their jurisdiction.""",
            percentile,
        )
    else:
        percentile = ((agency_fee_average / jurisdiction_fee_average) - 1) * 100
        return assign_grade(
            "fail",
            """On average, they charge {}% higher fees
            than other agencies in their jurisdiction.""",
            percentile,
        )
