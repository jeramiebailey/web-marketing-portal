from test_plus.test import TestCase
from notifications.models import Notification
from . import test_models
from django.utils import timezone
from django.urls import reverse
# from whatever.forms import WhateverForm
from django.contrib.auth.models import User
from django.test import RequestFactory, Client

client = Client()

# Not currently using Django view for this

# class NotificationViewTest(TestCase):

#     def setUp(self):
#         self.user = self.make_user()
#         self.factory = RequestFactory()

#     def test_whatever_list_view(self):
#         w = test_models.NotificationTest.create_notification(self)
#         url = reverse("notification.views.notification")
#         resp = self.client.get(url)

#         self.assertEqual(resp.status_code, 200)
#         self.assertIn(w.text, resp.content)