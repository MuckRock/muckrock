"""
Tests for Q&A
"""

# Django
from django.core import mail
from django.test import RequestFactory, TestCase
from django.urls import reverse

# MuckRock
from muckrock.core.factories import AnswerFactory, QuestionFactory, UserFactory
from muckrock.core.test_utils import mock_middleware
from muckrock.qanda.views import QuestionList, block_user, report_spam


class TestQandA(TestCase):
    """Test for Q&A"""

    def setUp(self):
        mail.outbox = []

    def test_answer_authors(self):
        """Test answer authors returns correct users"""
        question = QuestionFactory()
        answer1 = AnswerFactory(question=question, user__username="Alice")
        answer2 = AnswerFactory(question=question, user__username="Bob")
        AnswerFactory(
            question=question, user__username="Charlie", user__is_active=False
        )
        AnswerFactory(question=question, user=answer1.user)
        assert set(question.answer_authors()) == set([answer1.user, answer2.user])

    def test_block_user(self):
        """Test blocking a user"""
        question = QuestionFactory()
        url = reverse(
            "question-block", kwargs={"model": "question", "model_pk": question.pk}
        )
        request = RequestFactory().get(url)
        request = mock_middleware(request)
        request.user = UserFactory(is_staff=True)

        assert question.user.is_active
        block_user(request, "question", question.pk)
        question.user.refresh_from_db()
        assert not question.user.is_active
        assert len(mail.outbox) == 1

    def test_report_spam(self):
        """Test reporting spam"""
        answer = AnswerFactory()
        url = reverse(
            "question-spam", kwargs={"model": "answer", "model_pk": answer.pk}
        )
        request = RequestFactory().get(url)
        request = mock_middleware(request)
        request.user = UserFactory()

        assert answer.user.is_active
        report_spam(request, "answer", answer.pk)
        answer.refresh_from_db()
        assert answer.user.is_active
        assert len(mail.outbox) == 1

    def test_get_question_index(self):
        """Get the question index view"""
        request = RequestFactory().get(reverse("question-index"))
        request = mock_middleware(request)
        request.user = UserFactory()
        response = QuestionList.as_view()(request)
        assert response.status_code == 200
