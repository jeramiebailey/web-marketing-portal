from rest_framework.test import APIRequestFactory, force_authenticate, APIClient, APITestCase
from rest_framework import status
from docker_drf_backend.users.models import User
from docker_drf_backend.users.tests.factories import UserFactory
from organizations.tests.test_models import OrganizationTest
from guardian.shortcuts import assign_perm, remove_perm

class AccountHealthTests(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.user.is_staff = True
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = '/api/account-health-overviews/'

        organization_init = OrganizationTest()
        organization_init.setUp()
        self.organization = organization_init.test_create_organization()

    # def test_overdue_approvals_view(self):
    #     assign_perm('view_accounthealth', self.user, self.organization.account_health)
    #     endpoint = f'{self.url}{self.organization.account_health.id}/get_overdue_approvals/'
    #     print('endpoint is: ', endpoint)
    #     response = self.client.get(endpoint)
 
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(isinstance(response.data, list), True)