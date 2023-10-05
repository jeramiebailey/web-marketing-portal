from rest_framework.test import APIRequestFactory, force_authenticate, APIClient, APITestCase
from content_management.models import PlanningYearMonth
from docker_drf_backend.users.models import User
from reporting.views import ValidateMonthlyReportDataView
from rest_framework import status
from reporting.models import MonthlyReport, ReportEmailEntry
from reporting.tests.test_models import MonthlyReportTestCase, ReportEmailEntryTest
from organizations.tests.test_models import OrganizationTest
from content_management.tests.test_models import PlanningYearMonthTestCase
from docker_drf_backend.users.tests.factories import UserFactory

class MonthlyReportTests(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.user.is_staff = True
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        organization_init = OrganizationTest()
        organization_init.setUp()

        planning_year_month_init = PlanningYearMonthTestCase()
        planning_year_month_init.setUp()

        self.organization = organization_init.test_create_organization()
        self.planning_year_month = planning_year_month_init.test_create_planning_year_month()

        new_reports = self.planning_year_month.create_monthly_reports()

    def test_validate_data_debug_mode(self):
        url = '/api/validate-monthly-report-data/?debug_mode=True'
        data = {'planning_month': self.planning_year_month.id}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["debug_mode"], True)

    def test_unsent_report_notification(self):
        url = '/api/query-unsent-reports/?debug_mode=True'
        data = {'planning_month': self.planning_year_month.id}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sent_slack_message"], True)
        self.assertEqual(response.data["sent_email_notification"], True)


class ReportEmailEntryTests(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.user.is_staff = True
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = '/api/report-email-entries/'
        report_init = MonthlyReportTestCase()
        report_init.setUp()
        self.report = report_init.test_create_monthly_report()

    def test_create_entry(self):
        data = {
            'email': self.user.email,
            'report': self.report.id
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_entries(self):
        response = self.client.get(self.url)
        print('response.data is: ', response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(isinstance(response.data, list), True)
