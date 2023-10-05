from test_plus.test import TestCase, RequestFactory
from docker_drf_backend.users.tests.factories import UserFactory
from account_health.models import AccountHealth
from organizations.tests.test_models import OrganizationTest

class AccountHealthTest(TestCase):
    def setUp(self):
        self.rq = RequestFactory()
        organization_init = OrganizationTest()
        organization_init.setUp()
        self.organization = organization_init.test_create_organization()

    def test_create_account_health_object(self):
        created_object = self.organization.account_health
        self.assertTrue(isinstance(created_object, AccountHealth))
        return created_object

    def test_account_health_object(self):
        instance = self.test_create_account_health_object()
        self.assertTrue(isinstance(instance, AccountHealth))

    # def test_get_reporting_data(self):
    #     instance = self.test_create_account_health_object()
    #     lead_data = instance.get_leads_over_time_data()
    #     organic_traffic_data = instance.get_organic_traffic_data()