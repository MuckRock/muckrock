"""Tests for the browser-native date inputs"""

# Django
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

# Standard Library
import re
from datetime import date, timedelta

# MuckRock
from muckrock.core.filters import DateRangeWidget
from muckrock.core.forms import NativeDateInput
from muckrock.foia.filters import FOIALogEntryFilterSet
from muckrock.foia.forms import FOIAEmbargoForm
from muckrock.foia.forms.detail import FOIAEstimatedCompletionDateForm
from muckrock.foia.models import FOIALogEntry


def attrs(html, name):
    """The attributes of the input called `name` in `html`"""
    tag = re.search(rf'<input[^>]*name="{name}"[^>]*>', html).group(0)
    return dict(re.findall(r'(\w+)="([^"]*)"', tag))


def test_renders_a_date_input_with_an_iso_value():
    html = NativeDateInput().render("day", date(2024, 3, 9))

    assert attrs(html, "day") == {"type": "date", "name": "day", "value": "2024-03-09"}


def test_shows_dates_from_bookmarked_mm_dd_yyyy_urls():
    html = NativeDateInput().render("day", "11/04/2021")

    assert attrs(html, "day")["value"] == "2021-11-04"


def test_works_out_min_and_max_when_rendered():
    widget = NativeDateInput(attrs={"min": date.today, "max": date(2030, 1, 1)})

    found = attrs(widget.render("day", None), "day")

    assert found["min"] == date.today().isoformat()
    assert found["max"] == "2030-01-01"


def test_date_range_filters_render_two_date_inputs():
    html = DateRangeWidget().render("date_range", ["2024-01-02", "11/04/2021"])

    assert attrs(html, "date_range_min") == {
        "type": "date",
        "name": "date_range_min",
        "value": "2024-01-02",
    }
    assert attrs(html, "date_range_max")["value"] == "2021-11-04"


def test_date_range_filters_accept_iso_and_bookmarked_dates():
    request = RequestFactory().get("/")
    request.user = AnonymousUser()
    for start, end in [("2021-11-04", "2025-11-12"), ("11/04/2021", "11/12/2025")]:
        filterset = FOIALogEntryFilterSet(
            {"date_requested_min": start, "date_requested_max": end},
            queryset=FOIALogEntry.objects.none(),
            request=request,
        )

        assert filterset.form.is_valid(), filterset.form.errors
        span = filterset.form.cleaned_data["date_requested"]
        assert (span.start.date(), span.stop.date()) == (
            date(2021, 11, 4),
            date(2025, 11, 12),
        )


def test_embargo_date_is_limited_to_the_next_30_days():
    today = date.today()
    form = FOIAEmbargoForm(initial={"date_embargo": today + timedelta(5)})

    found = attrs(str(form["date_embargo"]), "date_embargo")

    assert found["type"] == "date"
    assert found["min"] == today.isoformat()
    assert found["max"] == (today + timedelta(30)).isoformat()
    assert found["value"] == (today + timedelta(5)).isoformat()


def test_embargo_form_accepts_the_iso_date_a_date_input_submits():
    expires = date.today() + timedelta(10)

    form = FOIAEmbargoForm({"date_embargo": expires.isoformat()})

    assert form.is_valid(), form.errors
    assert form.cleaned_data["date_embargo"] == expires


def test_estimated_completion_date_cannot_be_in_the_past():
    found = attrs(
        str(FOIAEstimatedCompletionDateForm()["date_estimate"]), "date_estimate"
    )

    assert found["type"] == "date"
    assert found["min"] == date.today().isoformat()
    assert "max" not in found
