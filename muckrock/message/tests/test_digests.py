"""
Test the message digests.
These will tell us if digests are
correctly grabbing site activity.
"""

# Django
from django.test import TestCase

# Standard Library
from datetime import date

# Third Party
import nose.tools
from actstream.actions import follow
from dateutil.relativedelta import relativedelta

# MuckRock
from muckrock.factories import (
    AgencyFactory,
    AnswerFactory,
    QuestionFactory,
    StatisticsFactory,
    UserFactory,
)
from muckrock.foia.factories import FOIARequestFactory
from muckrock.message import digests
from muckrock.utils import new_action, notify

ok_ = nose.tools.ok_
eq_ = nose.tools.eq_
raises = nose.tools.raises


class TestDailyDigest(TestCase):
    """Tests the ActivityDigest."""

    def setUp(self):
        self.user = UserFactory()
        self.digest = digests.ActivityDigest
        self.interval = relativedelta(days=1)

    def test_init(self):
        """The email should create when given a User."""
        ok_(self.digest(user=self.user, interval=self.interval))

    @raises(NotImplementedError)
    def test_requires_user(self):
        """The email should raise an error when instantiated without a user."""
        self.digest(user=None, interval=self.interval)

    def test_send_no_notifications(self):
        """The email shouldn't send if there's no notifications."""
        email = self.digest(user=self.user, interval=self.interval)
        eq_(email.activity['count'], 0, 'There should be no activity.')
        eq_(email.send(), 0, 'The email should not send.')

    def test_send_notification(self):
        """The email should send if there are notifications."""
        # generate an action on an actor the user follows
        agency = AgencyFactory()
        foia = FOIARequestFactory(agency=agency)
        action = new_action(agency, 'completed', target=foia)
        notify(self.user, action)
        # generate the email, which should contain the generated action
        email = self.digest(user=self.user, interval=self.interval)
        eq_(email.activity['count'], 1, 'There should be activity.')
        eq_(email.send(), 1, 'The email should send.')

    def test_digest_follow_requests(self):
        """Digests should include information on requests I follow."""
        # generate an action on a request the user owns
        other_user = UserFactory()
        foia = FOIARequestFactory(composer__user=other_user)
        agency = AgencyFactory()
        action = new_action(agency, 'rejected', target=foia)
        notify(self.user, action)
        # generate the email, which should contain the generated action
        email = self.digest(user=self.user, interval=self.interval)
        eq_(email.activity['count'], 1, 'There should be activity.')
        eq_(email.send(), 1, 'The email should send.')

    def test_digest_user_questions(self):
        """Digests should include information on questions I asked."""
        # generate an action on a question the user asked
        question = QuestionFactory(user=self.user)
        other_user = UserFactory()
        AnswerFactory(user=other_user, question=question)
        # creating an answer _should_ have created a notification
        # so let's generate the email and see what happened
        email = self.digest(user=self.user, interval=self.interval)
        eq_(
            email.activity['count'], 1,
            'There should be activity that is not user initiated.'
        )
        eq_(
            email.activity['questions']['mine'].first().action.actor, other_user
        )
        eq_(email.activity['questions']['mine'].first().action.verb, 'answered')
        eq_(email.send(), 1, 'The email should send.')

    def test_digest_follow_questions(self):
        """Digests should include information on questions I follow."""
        # generate an action on a question that I follow
        question = QuestionFactory()
        follow(self.user, question, actor_only=False)
        other_user = UserFactory()
        answer = AnswerFactory(user=other_user, question=question)
        email = self.digest(user=self.user, interval=self.interval)
        eq_(email.activity['count'], 1, 'There should be activity.')
        eq_(
            email.activity['questions']['following'].first().action.actor,
            other_user
        )
        eq_(
            email.activity['questions']['following'].first()
            .action.action_object, answer
        )
        eq_(
            email.activity['questions']['following'].first().action.target,
            question
        )
        eq_(email.send(), 1, 'The email should send.')


class TestStaffDigest(TestCase):
    """The Staff Digest updates us about the state of the website."""

    def setUp(self):
        self.user = UserFactory(is_staff=True)
        interval = relativedelta(days=1)
        yesterday = date.today() - interval
        day_before_yesterday = yesterday - interval
        week_before_yesterday = yesterday - relativedelta(weeks=1)
        month_before_yesterday = yesterday - relativedelta(months=1)

        StatisticsFactory(date=yesterday)
        StatisticsFactory(date=day_before_yesterday)
        StatisticsFactory(date=week_before_yesterday)
        StatisticsFactory(date=month_before_yesterday)

    def test_send(self):
        """The digest should send to staff members without errors."""
        digest = digests.StaffDigest(user=self.user)
        eq_(digest.send(), 1)

    def test_not_staff(self):
        """The digest should not send to users who are not staff."""
        not_staff = UserFactory()
        digest = digests.StaffDigest(user=not_staff)
        eq_(digest.send(), 0)
