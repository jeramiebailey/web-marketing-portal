from test_plus.test import TestCase, RequestFactory
from django.test.client import RequestFactory
from reporting.models import MonthlyReport, ReportEmailEntry
from organizations.tests.test_models import OrganizationTest
from content_management.tests.test_models import PlanningYearMonthTestCase
from django.conf import settings
from docker_drf_backend.users.tests.factories import UserFactory
from organizations.models import Organization
from django.utils import timezone

class MonthlyReportTestCase(TestCase):
    def setUp(self):
        self.rq = RequestFactory()
        organization_init = OrganizationTest()
        organization_init.setUp()

        planning_year_month_init = PlanningYearMonthTestCase()
        planning_year_month_init.setUp()

        self.organization = organization_init.test_create_organization()
        self.planning_year_month = planning_year_month_init.test_create_planning_year_month()

    def test_create_monthly_report(self):
        return MonthlyReport.objects.create(
            organization=self.organization,
            month=self.planning_year_month
        )

    def test_monthly_report(self):
        test_instance = self.test_create_monthly_report()
        self.assertTrue(isinstance(test_instance, MonthlyReport))
        self.assertEqual(test_instance.__str__(), f'{test_instance.id}')


class ReportEmailEntryTest(TestCase):
    def setUp(self):
        self.rq = RequestFactory()
        report_init = MonthlyReportTestCase()
        report_init.setUp()

        self.report = report_init.test_create_monthly_report()
        self.user = UserFactory()

    def test_create_report_email_entry(self):
        return ReportEmailEntry.objects.create(
            email=self.user.email,
            report=self.report,
            date_sent=timezone.now()
        )

    def test_report_email_entry(self):
        test_instance = self.test_create_report_email_entry()
        self.assertTrue(isinstance(test_instance, ReportEmailEntry))
        self.assertEqual(test_instance.__str__(), f'{test_instance.email} | {test_instance.uuid}')