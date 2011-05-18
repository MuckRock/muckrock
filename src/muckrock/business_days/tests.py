"""
Tests using nose for the business_days application
"""

from django.test import TestCase

import nose.tools
from datetime import date

from business_days import leap_year, days_in_month, calendars, HolidayDate, HolidayOrdWeekday

JAN, FEB, MAR, APR, MAY, JUN, JUL, AUG, SEP, OCT, NOV, DEC = range(1, 13)
MON, TUES, WEDS, THURS, FRI, SAT, SUN = range(0, 7)

# allow long names, methods that could be functions and too many public methods in tests
# pylint: disable-msg=C0103
# pylint: disable-msg=R0201
# pylint: disable-msg=R0904

class TestBusinessDayUnit(TestCase):
    """Unit tests for business days"""

    def setUp(self):
        """Set up tests"""
        self.new_years = HolidayDate("New Year's Day", JAN, 1)
        self.mlk_day = HolidayOrdWeekday('Martin Luther King, Jr. Day', JAN, MON, 3)

    def test_leap_year(self):
        """Test for leap years"""

        nose.tools.assert_true(leap_year(1996))
        nose.tools.assert_true(leap_year(2000))
        nose.tools.assert_false(leap_year(2002))
        nose.tools.assert_false(leap_year(2100))

    def test_days_in_month(self):
        """Test for how many days are in a month"""

        nose.tools.eq_(days_in_month(FEB, 1996), 29)
        nose.tools.eq_(days_in_month(FEB, 1997), 28)
        nose.tools.eq_(days_in_month(MAR, 1997), 31)

    def test_holiday_date_match(self):
        """Test matching for a holiday that occurs on a specific date"""

        nose.tools.assert_true(self.new_years.match(date(2010, 1, 1)))
        nose.tools.assert_false(self.new_years.match(date(2010, 2, 1)))

    def test_holiday_date_for_year(self):
        """Test retrieving the date for a holiday that occurs on a specific date of the year"""

        nose.tools.eq_(self.new_years.for_year(2010), date(2010, 1, 1))

    def test_holiday_ord_weekday_match(self):
        """Test matching for a holiday that occurs on a nth weekday of the month"""

        nose.tools.assert_true(self.mlk_day.match(date(2010, 1, 18)))
        nose.tools.assert_false(self.mlk_day.match(date(2010, 2, 18)))

    def test_holiday_ord_weekday_for_year(self):
        """Test retrieving the date for a holiday that occurs on a nth weekday of the month"""

        nose.tools.eq_(self.mlk_day.for_year(2010), date(2010, 1, 18))

    def test_holiday_calendars_is_holiday(self):
        """Test is_holiday"""

        nose.tools.assert_true(calendars['USA'].is_holiday(date(2011, 7, 4)))
        nose.tools.assert_false(calendars['USA'].is_holiday(date(2011, 7, 5)))

    def test_holiday_calendars_is_business_day(self):
        """Test is_business_day"""

        nose.tools.assert_false(calendars['USA'].is_business_day(date(2011, 7, 4)))
        nose.tools.assert_true(calendars['USA'].is_business_day(date(2011, 7, 5)))
        # weekend
        nose.tools.assert_false(calendars['USA'].is_business_day(date(2011, 7, 10)))

    def test_business_days_from(self):
        """Test business_days_from"""

        nose.tools.eq_(calendars['USA'].business_days_from(date(2010, 11, 1), 30),
                       date(2010, 12, 15))

    def test_business_days_between(self):
        """Test business_days_between"""

        nose.tools.eq_(calendars['USA'].business_days_between(date(2010, 11, 1),
                                                              date(2010, 12, 15)), 30)
