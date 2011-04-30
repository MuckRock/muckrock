"""
Calculate government business days and holidays
"""

from datetime import date, timedelta

JAN, FEB, MAR, APR, MAY, JUN, JUL, AUG, SEP, OCT, NOV, DEC = range(1, 13)
MON, TUES, WEDS, THURS, FRI, SAT, SUN = range(0, 7)

def leap_year(year):
    """Is the year a leap year?"""

    return not (year % 400) or (year % 100 and not year % 4)

def days_in_month(month, year):
    """How many days are in the month"""

    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    if month == FEB:
        return 29 if leap_year(year) else 28
    return days[month - 1]


class HolidayDate(object):
    """A Holiday that always occurs on the same date"""

    def __init__(self, name, month, day):
        self.name = name
        self.month = month
        self.day = day
        self.observe_sat = False

    def match(self, date_):
        """Is the given date an instance of this Holiday?"""

        # if the holiday falls on a Sun, observe on Mon
        # if it falls on Sat, move to Fri is observe_sat is False
        weekday = date_.weekday()
        if weekday == SUN or (weekday == SAT and not self.observe_sat):
            return False

        alt_date = None
        if weekday == MON:
            alt_date = date_ - timedelta(1)
        if weekday == FRI and not self.observe_sat:
            alt_date = date_ + timedelta(1)

        return (date_.day == self.day and date_.month == self.month) or \
               (alt_date and \
                alt_date.day == self.day and alt_date.month == self.month)

    def for_year(self, year):
        """Return the holiday's date for the given year"""

        date_ = date(year, self.month, self.day)
        weekday = date_.weekday()
        if weekday == SAT and not self.observe_sat:
            return date_ - timedelta(1)
        elif weekday == SUN:
            return date_ + timedelta(1)
        else:
            return date_


class HolidayOrdWeekday(object):
    """A Holiday that occurs on the nth weekday of a month"""

    def __init__(self, name, month, weekday, num):
        self.name = name
        self.month = month
        self.weekday = weekday
        self.num = num
        if not self.num:
            raise ValueError('n must be a non-zero integer')

    def match(self, date_):
        """Is the given date an instance of this Holiday?"""

        if date_.month == self.month and date_.weekday() == self.weekday:
            if self.num > 0:
                return (date_.day - 1) / 7 + 1 == self.num
            elif self.num < 0:
                days = days_in_month(date_.month, date_.year)
                return (days - date_.day) / 7 + 1 == -self.num

    def for_year(self, year):
        """Return the holiday's date for the given year"""

        if self.num > 0:
            first_date = date(year, self.month, 1)
            first = (self.weekday - first_date.weekday()) % 7 + 1
            day = first + 7 * (self.num - 1)
        elif self.num < 0:
            days = days_in_month(self.month, year)
            last_date = date(year, self.month, days)
            last = days + (self.weekday - last_date.weekday()) % -7
            day = last - 7 * (-self.num - 1)

        return date(year, self.month, day)


class ElectionDay(HolidayOrdWeekday):
    """Election day is the first Tuesday of November after Novermber 1"""

    def __init__(self):
        super(ElectionDay, self).__init__('Election Day', NOV, TUES, 1)

    def match(self, date_):
        """Is the given date an instance of this Holiday?"""

        return date_.month == NOV and date_.weekday() == TUES and \
               date_.day >= 2 and date_.day <= 8

    def for_year(self, year):
        """Return the holiday's date for the given year"""

        date_ = super(ElectionDay, self).for_year(year)
        if date_.day == 1:
            return date_.replace(day=8)
        else:
            return date_


class HolidayCalender(object):
    """A set of holidays"""

    def __init__(self, holidays, observe_sat):
        self.holidays = holidays
        self.observe_sat = observe_sat

        for holiday in self.holidays:
            holiday.observe_sat = observe_sat

    def is_holiday(self, date_):
        """Is given date a holiday?"""

        for holiday in self.holidays:
            if holiday.match(date_):
                return holiday
        return None

    def is_business_day(self, date_):
        """Is the given date a business day?"""

        weekday = date_.weekday()
        if weekday == SAT or weekday == SUN:
            return False

        return not self.is_holiday(date_)

    def busines_days_from(self, date_, num):
        """Returns the date n business days from the given date"""

        # could be further optimized
        while num:
            date_ += timedelta(1)
            if self.is_business_day(date_):
                num -= 1
        return date_

    def business_days_between(self, date_a, date_b):
        """How many business days are between the given dates?"""

        # could be optimized
        if date_a > date_b:
            date_a, date_b = date_b, date_a

        num = 0
        while date_a < date_b:
            date_a += timedelta(1)
            if self.is_business_day(date_a):
                num += 1
        return num

us_holidays = [
    HolidayDate("New Year's Day", JAN, 1),
    HolidayOrdWeekday('Martin Luther King, Jr. Day', JAN, MON, 3),
    HolidayOrdWeekday("Washington's Birthday", FEB, MON, 3),
    HolidayOrdWeekday('Memorial Day', MAY, MON, -1),
    HolidayDate('Independence Day', JUL, 4),
    HolidayOrdWeekday('Labor Day', SEP, MON, 1),
    HolidayOrdWeekday('Columbus Day', OCT, MON, 2),
    HolidayDate('Veterans Day', NOV, 11),
    HolidayOrdWeekday('Thanksgiving', NOV, THURS, 4),
    HolidayDate('Christmas', DEC, 25),
    ]

calenders = {
    'USA': HolidayCalender(us_holidays, False),
    'FL': HolidayCalender(us_holidays + [
            HolidayOrdWeekday('Day after Thanksgiving', NOV, FRI, 4)], False),
    'MA': HolidayCalender(us_holidays + [
            HolidayOrdWeekday("Patriots' Day", APR, MON, 3)], True),
    'ME': HolidayCalender(us_holidays + [
            HolidayOrdWeekday("Patriot's Day", APR, MON, 3)], False),
    'NY': HolidayCalender(us_holidays + [
            HolidayDate("Lincoln's Birthday", FEB, 12),
            ElectionDay()], True),
}
