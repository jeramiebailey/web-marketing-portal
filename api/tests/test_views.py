import json
from rest_framework import status
from django.test import Client
from test_plus.test import TestCase
from django.urls import reverse
from notifications.models import Notification
from api.views import NotificationViewSet
from ..serializers import NotificationSerializer
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate   

client = APIClient()

# class ViewSetTest(TestCase):
#     def setUp(self):
#         self.user = self.make_user()
#         self.factory = APIRequestFactory()
#         request = self.factory.post('/api/notifications/', {'text': 'new notification'}, format='json')
#         force_authenticate(request, user=self.user)

#     def test_view(self):
#         user = self.user
#         client.force_authenticate(user=user)
#         url = reverse('api:notifications-list')
#         data = {
#             'text': 'new notification',
#         }
#         response = client.post(url, data, format='json')

#         assert 201 == response.status_code