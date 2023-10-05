import pytest
from django.conf import settings
from django.test import RequestFactory
from rest_framework.test import APIRequestFactory, force_authenticate, APIClient, APITestCase
from docker_drf_backend.users.views import UserRedirectView, UserUpdateView
from docker_drf_backend.users.tests.factories import UserFactory
from rest_framework import status
from rest_auth.models import TokenModel

pytestmark = pytest.mark.django_db

class LoginViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = UserFactory()
        self.user.set_password('321testing')
        self.user.is_superuser = True
        self.user.save()

        self.end_user = UserFactory()
        self.end_user.set_password('321testing')
        self.end_user.save()

    def test_ghost_user_mode(self):
        self.end_user_client = APIClient()
        self.end_user_client.login(username=self.end_user.username, password='321testing')
        end_user_session = self.end_user_client.session
        end_user_session.save()

        url = f'/api/rest-auth/login/?as={self.end_user.username}'
        data = {
            'username': self.user.username,
            'password': '321testing',
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["ghost_user"])
        self.assertIsNotNone(response.data["ghost_user_token"])


# class TestUserUpdateView:
#     """
#         extracting view initialization code as class-scoped fixture
#         would be great if only pytest-django supported non-function-scoped
#         fixture db access -- this is a work-in-progress for now:
#         https://github.com/pytest-dev/pytest-django/pull/258
#     """

#     def test_get_success_url(
#         self, user: settings.AUTH_USER_MODEL, request_factory: RequestFactory
#     ):
#         view = UserUpdateView()
#         request = request_factory.get("/fake-url/")
#         request.user = user

#         view.request = request

#         assert view.get_success_url() == f"/users/{user.username}/"

#     def test_get_object(
#         self, user: settings.AUTH_USER_MODEL, request_factory: RequestFactory
#     ):
#         view = UserUpdateView()
#         request = request_factory.get("/fake-url/")
#         request.user = user

#         view.request = request

#         assert view.get_object() == user


# class TestUserRedirectView:

#     def test_get_redirect_url(
#         self, user: settings.AUTH_USER_MODEL, request_factory: RequestFactory
#     ):
#         view = UserRedirectView()
#         request = request_factory.get("/fake-url")
#         request.user = user

#         view.request = request

#         assert view.get_redirect_url() == f"/users/{user.username}/"
