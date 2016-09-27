"""
Tests for Jurisdiction application
"""

from django.core.urlresolvers import reverse
from django.test import TestCase

from datetime import date, timedelta
import nose.tools
from nose.tools import eq_

from muckrock.jurisdiction import factories
from muckrock.factories import (
        FOIARequestFactory,
        FOIACommunicationFactory,
        FOIAFileFactory,
        StateJurisdictionFactory,
        LocalJurisdictionFactory,
        )

# pylint: disable=no-self-use

class TestJurisdictionUnit(TestCase):
    """Unit tests for Jurisdictions"""

    def test_jurisdiction_unicode(self):
        """Test Jurisdiction model's __unicode__ method"""
        state = StateJurisdictionFactory(name='Massachusetts', abbrev='MA')
        local = LocalJurisdictionFactory(name='Boston', parent=state)
        nose.tools.eq_(unicode(state), u'Massachusetts')
        nose.tools.eq_(unicode(local), u'Boston, MA')

    def test_jurisdiction_url(self):
        """Test Jurisdiction model's get_absolute_url method"""
        state = StateJurisdictionFactory()
        nose.tools.eq_(state.get_absolute_url(),
            reverse('jurisdiction-detail',
                    kwargs={
                        'state_slug': state.slug,
                        'fed_slug': state.parent.slug}))

    def test_jurisdiction_legal(self):
        """Test Jurisdiction model's legal method"""
        state = StateJurisdictionFactory(name='Massachusetts', abbrev='MA')
        local = LocalJurisdictionFactory(name='Boston', parent=state)
        nose.tools.eq_(state.legal(), 'MA')
        nose.tools.eq_(local.legal(), 'MA')

    def test_jurisdiction_get_days(self):
        """Test Jurisdiction model's get days method"""
        state = StateJurisdictionFactory(days=10)
        local = LocalJurisdictionFactory(parent=state, days=None)
        nose.tools.eq_(state.get_days(), 10)
        nose.tools.eq_(local.get_days(), 10)

    def test_average_response_time(self):
        """Test the RequestHelper average response time mixin method with Jurisdictions"""
        state = StateJurisdictionFactory()
        local = LocalJurisdictionFactory()
        FOIARequestFactory(
                jurisdiction=state,
                date_submitted=date.today() - timedelta(18),
                date_done=date.today())
        FOIARequestFactory(
                jurisdiction=state,
                date_submitted=date.today() - timedelta(6),
                date_done=date.today())

        nose.tools.eq_(state.average_response_time(), 12)
        nose.tools.eq_(local.average_response_time(), 0)

    def test_total_pages(self):
        """Test the RequestHelper total pages mixin method with Jurisdictions"""
        state = StateJurisdictionFactory()
        local = LocalJurisdictionFactory()
        FOIAFileFactory(
                foia__jurisdiction=state,
                pages=18)
        FOIAFileFactory(
                foia__jurisdiction=state,
                pages=6)

        nose.tools.eq_(state.total_pages(), 24)
        nose.tools.eq_(local.total_pages(), 0)


class TestLawModel(TestCase):
    """
    The Law model contains information about a jurisdiction's law concerning public records.
    It should contain outside references to information on the law.
    """
    def setUp(self):
        self.law = factories.LawFactory()

    def test_unicode(self):
        """The text representation of the law should be the name of the law."""
        eq_(unicode(self.law), self.law.name,
            'The text representation of the law should match the name of the law.')

    def test_absolute_url(self):
        """The absolute url of the law should be the url of its jurisdiction."""
        eq_(self.law.get_absolute_url(), self.law.jurisdiction.get_absolute_url(),
            'The absolute url of the law should match the url of its jurisdicition.')


class TestExemptionModel(TestCase):
    """
    The Exemption model should contain information about a single kind of exemption.
    For example, the Public Employment Applications for Washtington state.
    """
    def setUp(self):
        self.exemption = factories.ExemptionFactory()

    def test_unicode(self):
        """The text representation should be the name of the exemption and its jurisdiction."""
        eq_(unicode(self.exemption),
            u'%s exemption of %s' % (self.exemption.name, self.exemption.jurisdiction),
            'Should include the name of the exemption and the name of the jurisdiction.')

    def test_absolute_url(self):
        """The absolute url of the exemption should be a standalone exemption detail page."""
        kwargs = self.exemption.jurisdiction.get_slugs()
        kwargs['slug'] = self.exemption.slug
        kwargs['pk'] = self.exemption.pk
        expected_url = reverse('exemption-detail', kwargs=kwargs)
        actual_url = self.exemption.get_absolute_url()
        eq_(actual_url, expected_url, ('The exemption should return the exemption-detail url.\n'
             'Actual url: %s\nExpected url: %s') % (actual_url, expected_url))


class TestInvokedExemptionModel(TestCase):
    """
    The InvokedExemption model should contain information about a single invocation
    of an exemption. For example, when an agency in Washington state uses the
    Public Employment Applications exemption to withhold records from a request.
    """
    def setUp(self):
        self.invoked_exemption = factories.InvokedExemptionFactory()

    def test_unicode(self):
        """The text representation should be the names of the exemption and the request."""
        actual = unicode(self.invoked_exemption)
        expected = u'%s exemption of %s' % (
            self.invoked_exemption.exemption.name,
            self.invoked_exemption.request,
        )
        eq_(actual,
            expected,
            ('Should include the name of the exemption and the request.\n'
            'Actual: %s\nExpected: %s' % (actual, expected)))

    def test_absolute_url(self):
        """The absolute url of the invoked exemption should be the absolute url of the
        exemption with the invokation pk appended as a target."""
        exemption = self.invoked_exemption.exemption
        kwargs = exemption.jurisdiction.get_slugs()
        kwargs['slug'] = exemption.slug
        kwargs['pk'] = exemption.pk
        expected_url = (reverse('exemption-detail', kwargs=kwargs) +
                        '#invoked-%d' % self.invoked_exemption.pk)
        actual_url = self.invoked_exemption.get_absolute_url()
        eq_(actual_url,
            expected_url,
            ('The exemption should return the exemption-detail url.\n'
             'Actual url: %s\nExpected url: %s') % (actual_url, expected_url))


class TestExampleAppealModel(TestCase):
    """
    The ExampleAppeal model should contain sample language for appealing an exemption.
    Additionally, it should contain the context in which this language is most effective.
    """
    def setUp(self):
        self.example_appeal = factories.ExampleAppealFactory()

    def test_unicode(self):
        """The text representation should be the appeal's context and exemption."""
        actual = unicode(self.example_appeal)
        expected = u'%s for %s' % (self.example_appeal.context, self.example_appeal.exemption)
        eq_(actual,
            expected,
            ('Should include the name of the exemption and the request.\n'
            'Actual: %s\nExpected: %s' % (actual, expected)))

    def test_absolute_url(self):
        """The absolute url of the appeal language should be the absolute url of the exemption
        with the appeal pk appeneded as a target."""
        exemption = self.example_appeal.exemption
        kwargs = exemption.jurisdiction.get_slugs()
        kwargs['slug'] = exemption.slug
        kwargs['pk'] = exemption.pk
        expected_url = (reverse('exemption-detail', kwargs=kwargs) +
                        '#appeal-%d' % self.example_appeal.pk)
        actual_url = self.example_appeal.get_absolute_url()
        eq_(actual_url,
            expected_url,
            ('The exemption should return the exemption-detail url.\n'
             'Actual url: %s\nExpected url: %s') % (actual_url, expected_url))


class TestAppealModel(TestCase):
    """
    The Appeal model is used to track information about appeals when they are filed.
    An appeal should be able to judge whether or not it was successful.
    It should do this by analyzing the request's communication chain
    following the communication it corresponds to.
    """
    def setUp(self):
        self.appeal = factories.AppealFactory()

    def test_unicode(self):
        """The text representation should say which request the appeal is of."""
        actual = unicode(self.appeal)
        expected = u'Appeal of %s' % self.appeal.communication.foia
        eq_(actual, expected)

    def test_absolute_url(self):
        """The absolute url for the appeal should be the absolute url of the communication."""
        expected = self.appeal.communication.get_absolute_url()
        actual = self.appeal.get_absolute_url()
        eq_(expected, actual)

    def test_unsuccessful_by_default(self):
        """By default, an appeal should be not be successful."""
        eq_(self.appeal.is_successful(), False)

    def test_successful(self):
        """The appeal was successful if a subsequent communication has a 'Completed' status."""
        FOIACommunicationFactory(
            foia=self.appeal.communication.foia,
            status='done'
        )
        eq_(self.appeal.is_successful(), True)

    def test_another_appeal(self):
        """The appeal was unsuccessful if a subsequent communication has an Appeal as well."""
        subsequent_communication = FOIACommunicationFactory(
            foia=self.appeal.communication.foia,
            status='done'
        )
        factories.AppealFactory(communication=subsequent_communication)
        eq_(self.appeal.is_successful(), False)

    def test_unfinished_by_default(self):
        """By default, an appeal should not be finished."""
        eq_(self.appeal.is_finished(), False)

    def test_finished(self):
        """The appeal was finished if a subsequent communication has a terminal status."""
        FOIACommunicationFactory(
            foia=self.appeal.communication.foia,
            status='rejected'
        )
        eq_(self.appeal.is_finished(), True)
