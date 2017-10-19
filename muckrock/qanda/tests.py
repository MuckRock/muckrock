"""
Tests for Q&A
"""

from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory

import nose.tools

from muckrock.factories import (
        AnswerFactory,
        QuestionFactory,
        UserFactory,
        )
from muckrock.qanda.views import block_user, report_spam
from muckrock.test_utils import mock_middleware


class TestQandA(TestCase):
    """Test for Q&A"""
    # pylint: disable=no-self-use

    def setUp(self):
        mail.outbox = []

    def test_answer_authors(self):
        """Test answer authors returns correct users"""
        question = QuestionFactory()
        answer1 = AnswerFactory(
                question=question,
                user__username='Alice',
                )
        answer2 = AnswerFactory(
                question=question,
                user__username='Bob',
                )
        AnswerFactory(
                question=question,
                user__username='Charlie',
                user__is_active=False,
                )
        AnswerFactory(
                question=question,
                user=answer1.user,
                )
        nose.tools.eq_(
                set(question.answer_authors()),
                set([answer1.user, answer2.user]),
                )

    def test_block_user(self):
        """Test blocking a user"""
        question = QuestionFactory()
        url = reverse(
                'question-block',
                kwargs={
                    'model': 'question',
                    'model_pk': question.pk,
                    })
        request = RequestFactory().get(url)
        request = mock_middleware(request)
        request.user = UserFactory(is_staff=True)

        nose.tools.ok_(question.user.is_active)
        block_user(request, 'question', question.pk)
        question.user.refresh_from_db()
        print 'question user', question.user.pk, question.user.username
        nose.tools.assert_false(question.user.is_active)
        nose.tools.eq_(len(mail.outbox), 1)

    def test_report_spam(self):
        """Test reporting spam"""
        answer = AnswerFactory()
        url = reverse(
                'question-spam',
                kwargs={
                    'model': 'answer',
                    'model_pk': answer.pk,
                    })
        request = RequestFactory().get(url)
        request = mock_middleware(request)
        request.user = UserFactory()

        nose.tools.ok_(answer.user.is_active)
        report_spam(request, 'answer', answer.pk)
        answer.refresh_from_db()
        nose.tools.ok_(answer.user.is_active)
        nose.tools.eq_(len(mail.outbox), 1)
