from docker_drf_backend.taskapp.celery import app
from celery import shared_task
from account_health.models import AccountHealth

@app.task
def pull_account_health_analytics(object_id=None, organization_id=None):
    is_list = False
    if object_id:
        try:
            account_health_objects = AccountHealth.objects.get(id=object_id)
        except:
            account_health_objects = None

    elif organization_id:
        try:
            account_health_objects = AccountHealth.objects.get(account__id=organization_id)
        except:
            account_health_objects = None
    else:
        is_list = True
        account_health_objects = AccountHealth.objects.filter(account__is_active=True)

    if account_health_objects:
        if is_list:
            for account in account_health_objects:
                account.get_leads_over_time_data()
                account.get_organic_traffic_data()
        else:
            account_health_objects.get_leads_over_time_data()
            account_health_objects.get_organic_traffic_data()

@app.task
def pull_account_health_page_speed(object_id=None, organization_id=None):
    is_list = False
    if object_id:
        try:
            account_health_objects = AccountHealth.objects.get(id=object_id)
        except:
            account_health_objects = None

    elif organization_id:
        try:
            account_health_objects = AccountHealth.objects.get(account__id=organization_id)
        except:
            account_health_objects = None
    else:
        is_list = True
        account_health_objects = AccountHealth.objects.filter(account__is_active=True)

    if account_health_objects:
        if is_list:
            for account in account_health_objects:
                account.get_desktop_page_speed_data()
                account.get_mobile_page_speed_data()
        else:
            account_health_objects.get_desktop_page_speed_data()
            account_health_objects.get_mobile_page_speed_data()

@shared_task(name="pull_all_account_data")
def pull_all_account_data(object_id=None, organization_id=None):
    is_list = False
    if object_id:
        try:
            account_health_objects = AccountHealth.objects.get(id=object_id)
        except:
            account_health_objects = None

    elif organization_id:
        try:
            account_health_objects = AccountHealth.objects.get(account__id=organization_id)
        except:
            account_health_objects = None
    else:
        is_list = True
        account_health_objects = AccountHealth.objects.filter(account__is_active=True)

    if account_health_objects:
        if is_list:
            for account in account_health_objects:
                account.pull_all_account_data()
        else:
            account_health_objects.pull_all_account_data()