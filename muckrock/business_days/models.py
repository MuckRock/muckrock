"""
Models for the Business Days application
"""
# Django
from django.db import models

# Standard Library
from calendar import monthrange
from datetime import timedelta

# Third Party
from pascha import computus, traditions

JAN, FEB, MAR, APR, MAY, JUN, JUL, AUG, SEP, OCT, NOV, DEC = range(1, 13)
MON, TUES, WEDS, THURS, FRI, SAT, SUN = range(0, 7)


class Holiday(models.Model):
    """A holiday"""

    kinds = (
        ('date', 'Date'),
        ('ord_wd', 'Ordinal Weekday'),
        ('easter', 'Easter'),
        ('election', 'Election'),
    )

    # pylint: disable=bad-whitespace
    months = (
        (1, 'January'),
        (2, 'February'),
        (3, 'March'),
        (4, 'April'),
        (5, 'May'),
        (6, 'June'),
        (7, 'July'),
        (8, 'August'),
        (9, 'September'),
        (10, 'October'),
        (11, 'November'),
        (12, 'December'),
    )
    # pylint: enable=bad-whitespace

    weekdays = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )

    name = models.CharField(max_length=255)
    kind = models.CharField(max_length=8, choices=kinds)
    month = models.PositiveSmallIntegerField(
        choices=months,
        null=True,
        blank=True,
        help_text='Only used for date and ordinal weekday holidays'
    )
    # date
    day = models.PositiveSmallIntegerField(
        choices=zip(range(1, 32), range(1, 32)),
        null=True,
        blank=True,
        help_text='Only used for date holidays'
    )
    # ord weekday
    weekday = models.PositiveSmallIntegerField(
        choices=weekdays,
        null=True,
        blank=True,
        help_text='Only used for ordinal weekday holidays'
    )
    num = models.SmallIntegerField(
        null=True,
        blank=True,
        help_text='Only used for ordinal weekday holidays'
    )

    # easter and election day do not need any additional info

    def __unicode__(self):
        return self.name

    def match(self, date_, observe_sat):
        """Is the given date an instance of this Holiday?"""
        table = dict((k, getattr(self, '_match_%s' % k)) for k, _ in self.kinds)
        return table[self.kind](date_, observe_sat)

    def _match_date(self, date_, observe_sat):
        """match for date type holidays"""
        # if the holiday falls on a Sun, observe on Mon
        # if it falls on Sat, move to Fri if observe_sat is False
        weekday = date_.weekday()
        if weekday == SUN or (weekday == SAT and not observe_sat):
            return False

        alt_date = None
        if weekday == MON:
            alt_date = date_ - timedelta(1)
        if weekday == FRI and not observe_sat:
            alt_date = date_ + timedelta(1)

        return (date_.day == self.day and date_.month == self.month) or \
               (alt_date and \
                alt_date.day == self.day and alt_date.month == self.month)

    def _match_ord_wd(self, date_, _):
        """match for ord weekday type holidays"""

        if date_.month == self.month and date_.weekday() == self.weekday:
            if self.num > 0:
                return (date_.day - 1) / 7 + 1 == self.num
            elif self.num < 0:
                # get number of days in the month
                days = monthrange(date_.year, date_.month)[1]
                return (days - date_.day) / 7 + 1 == -self.num

    def _match_easter(self, date_, _):
        """match for easter based dates"""
        return date_ == traditions.Western.offset[self.name] + \
            computus.western(None, year=date_.year).date()

    def _match_election(self, date_, _):
        """match for election day"""
        return date_.month == NOV and date_.weekday() == TUES and \
               date_.day >= 2 and date_.day <= 8


class HolidayCalendar(object):
    """A set of holidays"""

    def __init__(self, holidays, observe_sat):
        self.holidays = holidays
        self.observe_sat = observe_sat

    def is_holiday(self, date_):
        """Is given date a holiday?"""

        for holiday in self.holidays:
            if holiday.match(date_, self.observe_sat):
                return holiday
        return None

    def is_business_day(self, date_):
        """Is the given date a business day?"""

        weekday = date_.weekday()
        if weekday == SAT or weekday == SUN:
            return False

        return not self.is_holiday(date_)

    def business_days_from(self, date_, num):
        """Returns the date n business days from the given date"""

        # could be optimized
        delta = timedelta(1 if num >= 0 else -1)
        num = abs(num)

        while num:
            date_ += delta
            if self.is_business_day(date_):
                num -= 1
        return date_

    def business_days_between(self, date_a, date_b):
        """How many business days are between the given dates?"""

        # could be optimized
        sign = 1
        if date_a > date_b:
            date_a, date_b = date_b, date_a
            sign = -1

        num = 0
        while date_a < date_b:
            date_a += timedelta(1)
            if self.is_business_day(date_a):
                num += 1
        return num * sign


class Calendar(object):
    """A set of holidays"""

    def is_holiday(self, _):
        """Is given date a holiday?"""
        return None

    def is_business_day(self, _):
        """Is the given date a business day?"""
        return True

    def business_days_from(self, date_, num):
        """Returns the date n business days from the given date"""
        return date_ + timedelta(num)

    def business_days_between(self, date_a, date_b):
        """How many business days are between the given dates?"""
        return abs((date_a - date_b).days)
