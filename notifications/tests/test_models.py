from test_plus.test import TestCase
from notifications.models import Notification
from django.utils import timezone
from django.urls import reverse
# from whatever.forms import WhateverForm
from django.contrib.auth.models import User
from django.test import RequestFactory

class NotificationTest(TestCase):

    def setUp(self):
        self.user = self.make_user()
        self.factory = RequestFactory()

    def create_notification(self, text="only a test"):
        return Notification.objects.create(text=text, owner=self.user, created_at=timezone.now())

    def test_notification_creation(self):
        w = self.create_notification()
        self.assertTrue(isinstance(w, Notification))
        self.assertEqual(w.__str__(), w.text)