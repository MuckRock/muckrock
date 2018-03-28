"""
Tests using nose for the business_days application
"""

# Django
from django.test import TestCase

# Standard Library
from datetime import date

# Third Party
import nose.tools

# MuckRock
from muckrock.business_days.models import Calendar, Holiday
from muckrock.jurisdiction.models import Jurisdiction


class TestBusinessDayUnit(TestCase):
    """Unit tests for business days"""

    # pylint: disable=invalid-name

    def setUp(self):
        """Set up tests"""
        self.new_years = Holiday.objects.get(name="New Year's Day")
        self.mlk_day = Holiday.objects.get(name='Martin Luther King, Jr. Day')
        self.good_friday = Holiday.objects.get(name='Good Friday')
        self.usa_cal = Jurisdiction.objects.get(
            name='United States of America'
        ).get_calendar()
        self.gen_cal = Calendar()

    def test_holiday_date_match(self):
        """Test matching for a holiday that occurs on a specific date"""

        nose.tools.assert_true(self.new_years.match(date(2010, 1, 1), False))
        nose.tools.assert_false(self.new_years.match(date(2010, 2, 1), False))

    def test_holiday_ord_weekday_match(self):
        """Test matching for a holiday that occurs on a nth weekday of the month"""

        nose.tools.assert_true(self.mlk_day.match(date(2010, 1, 18), False))
        nose.tools.assert_false(self.mlk_day.match(date(2010, 2, 18), False))

    def test_holiday_easter_match(self):
        """Test matching for a holiday that occurs based on Easter"""

        nose.tools.assert_true(self.good_friday.match(date(2010, 4, 2), False))
        nose.tools.assert_false(
            self.good_friday.match(date(2010, 4, 18), False)
        )

    def test_holiday_calendars_is_holiday(self):
        """Test is_holiday"""

        nose.tools.assert_true(self.usa_cal.is_holiday(date(2011, 7, 4)))
        nose.tools.assert_false(self.usa_cal.is_holiday(date(2011, 7, 5)))

    def test_holiday_calendars_is_business_day(self):
        """Test is_business_day"""

        nose.tools.assert_false(self.usa_cal.is_business_day(date(2011, 7, 4)))
        nose.tools.assert_true(self.usa_cal.is_business_day(date(2011, 7, 5)))
        # weekend
        nose.tools.assert_false(self.usa_cal.is_business_day(date(2011, 7, 10)))

    def test_business_days_from(self):
        """Test business_days_from"""

        nose.tools.eq_(
            self.usa_cal.business_days_from(date(2010, 11, 1), 30),
            date(2010, 12, 15)
        )

    def test_business_days_between(self):
        """Test business_days_between"""

        nose.tools.eq_(
            self.usa_cal.business_days_between(
                date(2010, 11, 1), date(2010, 12, 15)
            ), 30
        )

    def test_calendar_days_from(self):
        """Test business_days_from for calendar days"""

        nose.tools.eq_(
            self.gen_cal.business_days_from(date(2010, 11, 1), 30),
            date(2010, 12, 1)
        )

    def test_calendar_days_between(self):
        """Test business_days_between for calendar days"""

        nose.tools.eq_(
            self.gen_cal.business_days_between(
                date(2010, 11, 1), date(2010, 12, 1)
            ), 30
        )
