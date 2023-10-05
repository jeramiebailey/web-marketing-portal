from django.conf.urls import include, url
from django.urls import path
from rest_framework import routers
from django.conf import settings
from .views import *

app_name = "utilities"
urlpatterns = [
    path('check-broken-links/', CheckBrokenLinksView.as_view(), name="check_broken_links")
]