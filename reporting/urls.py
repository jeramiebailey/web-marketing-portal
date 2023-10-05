from django.conf.urls import include, url
from django.urls import path
from reporting.views import unsubscribe, unsubscribe_success, unsubscribe_failure

app_name = "reporting"
urlpatterns = [
    path('unsubscribe-success/<str:email_address>/<str:organization_name>/', unsubscribe_success, name="unsubscribe-success"),
    path('unsubscribe-failure/<str:email_address>/<str:organization_name>/', unsubscribe_failure, name="unsubscribe-failure"),
    path('unsubscribe/<uuid:uuid>/<str:email_address>/', unsubscribe, name="unsubscribe"),
]