from __future__ import print_function
import pickle
import os.path
import datetime
import calendar
from dateutil.relativedelta import *
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2 import service_account
# from google.analytics.data_v1alpha import AlphaAnalyticsDataClient
# from google.analytics.data_v1alpha.types import DateRange
# from google.analytics.data_v1alpha.types import Dimension
# from google.analytics.data_v1alpha.types import Entity
# from google.analytics.data_v1alpha.types import Metric
# from google.analytics.data_v1alpha.types import RunReportRequest

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange
from google.analytics.data_v1beta.types import Dimension
from google.analytics.data_v1beta.types import Metric
from google.analytics.data_v1beta.types import RunReportRequest

import os
import environ
import json
import requests
from celery.decorators import task
from docker_drf_backend.taskapp.celery import app

env = environ.Env()

content_generation_folder = env('CONTENT_GEN_FOLDER_ID')

what_converts_tto_token = env('WHAT_CONVERTS_TTO_TOKEN')
what_converts_tto_secret = env('WHAT_CONVERTS_TTO_SECRET')
what_converts_spt_token = env('WHAT_CONVERTS_SPT_TOKEN')
what_converts_spt_secret = env('WHAT_CONVERTS_SPT_SECRET')

module_dir = os.path.dirname(__file__)  # get current directory

SERVICE_ACCOUNT_FILE = os.path.join(module_dir, 'portal_v3_credentials.json')
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/analytics.readonly']
CREDENTIALS = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)


### Google Drive Functions

def create_drive_file(name, isFolder, parent=None):
    service = build('drive', 'v3', credentials=CREDENTIALS)
    if parent is None:
        parent_folder = content_generation_folder
    else:
        parent_folder = parent
    if isFolder:
        mime_type = 'application/vnd.google-apps.folder'
    else:
        mime_type = 'application/vnd.google-apps.document'
    file_metadata = {
        'name': name,
        'mimeType': mime_type,
        'parents': [parent_folder],
    }
    file = service.files().create(body=file_metadata, supportsTeamDrives=True).execute()
    file_id = file.get('id')
    return file_id


def search_drive_files(name, folder=None):
    if folder is None:
        parent_folder = content_generation_folder
    else:
        parent_folder = folder

    service = build('drive', 'v3', credentials=CREDENTIALS)

    search = service.files().list(q="(name = '{0}' and parents in '{1}')".format(name, parent_folder), supportsTeamDrives=True, includeTeamDriveItems=True).execute()
    if search['files']:
        return search['files'][0].get('id')
    else:
        return False

### Google Calendar Functions

def get_shared_calendar(resultNumber):
    service = build('calendar', 'v3', credentials=CREDENTIALS)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time

    events_result = service.events().list(calendarId='321legaldesign.com_gjka4gfg7oqqntr8mvc01a8jnk@group.calendar.google.com', 
                                        timeMin=now,
                                        maxResults=resultNumber, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])


### Google Analytics Functions

def get_ga4_report(property_id, start_month=None, start_year=None, months_back=6):
    client = BetaAnalyticsDataClient(credentials=CREDENTIALS)

    today = datetime.datetime.today()
    today_string = today.strftime("%Y-%m-%d")

    last_month = today + relativedelta(months=-1)
    last_month_string = last_month.strftime("%Y-%m-%d")

    if start_month is None: 
        start_month = int(today.strftime("%m"))

    if start_year is None:
        start_year = int(today.strftime("%Y"))

    initial_start_date = datetime.datetime(start_year, start_month, 1) + relativedelta(months=-1)
    initial_start_date_month = int(initial_start_date.strftime("%m"))
    initial_start_date_year = int(initial_start_date.strftime("%Y"))
    last_day_of_start_month = calendar.monthrange(initial_start_date_year, initial_start_date_month)[1]
    start_date = datetime.datetime(initial_start_date_year, initial_start_date_month, last_day_of_start_month)
    start_date_string = start_date.strftime("%Y-%m-%d")

    initial_end_date = start_date + relativedelta(months=-5)
    initial_end_date = start_date + relativedelta(months=-(months_back-1))
    end_date_month = int(initial_end_date.strftime("%m"))
    end_date_year = int(initial_end_date.strftime("%Y"))
    end_date = datetime.datetime(end_date_year, end_date_month, 1)
    end_date_string = end_date.strftime("%Y-%m-%d")
    
    ga_call = RunReportRequest(property=f"properties/{property_id}",
                               dimensions=[Dimension(name='sessionDefaultChannelGrouping'), Dimension(name='year'), Dimension(name='month')],
                               metrics=[Metric(name='newUsers')],
                               date_ranges=[DateRange(start_date=f"{end_date_string}",
                                                      end_date=f"{start_date_string}")])
    print(ga_call)                                                 
    response = client.run_report(ga_call)

    return response


def get_ga_report(view_id, start_month=None, start_year=None, months_back=6):
    analytics = build('analyticsreporting', 'v4', credentials=CREDENTIALS, cache_discovery=False)

    today = datetime.datetime.today()
    today_string = today.strftime("%Y-%m-%d")

    last_month = today + relativedelta(months=-1)
    last_month_string = last_month.strftime("%Y-%m-%d")

    if start_month is None:
        start_month = int(today.strftime("%m"))

    if start_year is None:
        start_year = int(today.strftime("%Y"))

    initial_start_date = datetime.datetime(start_year, start_month, 1) + relativedelta(months=-1)
    initial_start_date_month = int(initial_start_date.strftime("%m"))
    initial_start_date_year = int(initial_start_date.strftime("%Y"))
    last_day_of_start_month = calendar.monthrange(initial_start_date_year, initial_start_date_month)[1]
    start_date = datetime.datetime(initial_start_date_year, initial_start_date_month, last_day_of_start_month)
    start_date_string = start_date.strftime("%Y-%m-%d")

    initial_end_date = start_date + relativedelta(months=-5)
    initial_end_date = start_date + relativedelta(months=-(months_back-1))
    end_date_month = int(initial_end_date.strftime("%m"))
    end_date_year = int(initial_end_date.strftime("%Y"))
    end_date = datetime.datetime(end_date_year, end_date_month, 1)
    end_date_string = end_date.strftime("%Y-%m-%d")

    try:
        ga_call = analytics.reports().batchGet(
            body={
            "reportRequests": [
            {
                "viewId": view_id,
                "dateRanges": [
                    {
                        "startDate": f"{end_date_string}", "endDate": f"{start_date_string}"
                    },
                ],
                "metrics": [
                    {
                        "expression": "ga:newUsers"
                    }
                ],
                "dimensions": [
                    {
                        "name": "ga:channelGrouping",
                    },
                    {
                        "name": "ga:yearMonth"
                    }
                ]
            }]
            }
        ).execute()
    
    except:
        ga_call = None
    
    if ga_call:
        return ga_call
    else:
        print(f'ga_call failed with view_id of {view_id}')

@app.task
def get_ga4_report_data(property_id, start_month=None, start_year=None, months_back=6):
    print('get_ga4_report_data fired')
    try:
        response = get_ga4_report(property_id, start_month=start_month, start_year=start_year, months_back=months_back)
    except:
        response = None

    if response:
        data_rows = response.rows
        output = []
        
        for row in data_rows:
            source = row.dimension_values[0].value
            year = row.dimension_values[1].value
            month = row.dimension_values[2].value
            value = row.metric_values[0].value
            month_year = int(year)
            month_month = int(month)
            month_verbose = f'{calendar.month_abbr[month_month]} {month_year}'

            for obj in output:
                if obj['month'] == month_verbose:
                    if not obj['sources']:
                        obj['sources'] = []

                    obj['sources'].append({
                        'source': source,
                        'value': value
                    })

                    break
            
            else:
                new_month_object = {
                    'month': month_verbose,
                    'month_month': month_month,
                    'month_year': month_year,
                    'sources': []
                }

                new_month_object['sources'].append({
                    'source': source,
                    'value': value
                })
                output.append(new_month_object)
        
        try:
            output = sorted(output, key = lambda i: (i['month_year'], i['month_month']))
        except:
            pass

        print('get_ga4_report_data successful')
        return output

    else:
        output = f'get_report_data unsuccessful for property_id: {property_id}'
        print(output)
        return None



@app.task
def get_report_data(view_id, start_month=None, start_year=None, months_back=6):
    try:
        response = get_ga_report(view_id, start_month=start_month, start_year=start_year, months_back=months_back)
    except:
        response = None
    if response:
        report = response.get('reports')[0]
        data = report['data']
        data_rows = data['rows']

        output = []
        
        for row in data_rows:
            source = row['dimensions'][0]
            month = row['dimensions'][1]
            month_year = int(month[:4])
            month_month = int(month[-2:])
            month_verbose = f'{calendar.month_abbr[month_month]} {month_year}'
            value = row['metrics'][0]['values'][0]
                    
            for obj in output:
                if obj['month'] == month_verbose:
                    if not obj['sources']:
                        obj['sources'] = []

                    obj['sources'].append({
                        'source': source,
                        'value': value
                    })

                    break
            
            else:
                new_month_object = {
                    'month': month_verbose,
                    'month_month': month_month,
                    'month_year': month_year,
                    'sources': []
                }

                new_month_object['sources'].append({
                    'source': source,
                    'value': value
                })
                output.append(new_month_object)

        try:
            output = sorted(output, key = lambda i: (i['month_year'], i['month_month']))
        except:
            pass

        return output
    else:
        print(f'get_report_data unsuccessful for view_id: {view_id}')
        return None


## WhatConverts Functions

def pull_wc_lead_data(params, spt_account):
    if spt_account:
        auth = (f'{what_converts_spt_token}', f'{what_converts_spt_secret}')
    else:
        auth = (f'{what_converts_tto_token}', f'{what_converts_tto_secret}')

    url = "https://app.whatconverts.com/api/v1/leads"
    response = requests.get(url, auth=auth, params=params)
    data = json.loads(response.text)

    return data

@app.task
def get_whatconverts_data(account_id, start_month=None, start_year=None, spt_account=None, months_back=6):
    today = datetime.datetime.today()
    today_string = today.strftime("%Y-%m-%d")

    last_month = today + relativedelta(months=-1)
    last_month_string = last_month.strftime("%Y-%m-%d")

    if start_month is None:
        start_month = int(today.strftime("%m"))

    if start_year is None:
        start_year = int(today.strftime("%Y"))

    initial_end_date = datetime.datetime(start_year, start_month, 1) + relativedelta(months=-1)
    initial_end_date_month = int(initial_end_date.strftime("%m"))
    initial_end_date_year = int(initial_end_date.strftime("%Y"))
    last_day_of_end_month = calendar.monthrange(initial_end_date_year, initial_end_date_month)[1]
    end_date = datetime.datetime(initial_end_date_year, initial_end_date_month, last_day_of_end_month)
    end_date_string = end_date.strftime("%Y-%m-%d")

    initial_start_date = end_date + relativedelta(months=-(months_back-1))
    start_date_month = int(initial_start_date.strftime("%m"))
    start_date_year = int(initial_start_date.strftime("%Y"))
    start_date = datetime.datetime(start_date_year, start_date_month, 1)
    start_date_string = start_date.strftime("%Y-%m-%d")
    
    params = {
        "account_id": int(account_id),
        "start_date": start_date_string,
        "end_date": end_date_string,
        "lead_status": "unique",
        "leads_per_page": 1000,
        "order": "asc",
    }

    data = pull_wc_lead_data(params, spt_account)
    wc_lead_data = []

    try:
        total_pages = data['total_pages']
    except:
        total_pages = None

    try:
        lead_data = data['leads']
    except:
        lead_data = None

    if lead_data:
        wc_lead_data.extend(lead_data)

    if total_pages and total_pages > 1:
        for i in range(total_pages):
            new_params = params
            new_params['page_number'] = i + 1
            additional_data = pull_wc_lead_data(new_params, spt_account)

            try:
                additional_lead_data = additional_data['leads']
            except:
                additional_lead_data = None

            if additional_lead_data:
                wc_lead_data.extend(additional_lead_data)

    if wc_lead_data:
        total_leads = data['total_leads']
        output = []

        for lead in wc_lead_data:
            lead_type = lead['lead_type']
            date_created = lead['date_created']
            quotable = lead['quotable']
            month_year = int(date_created[:4])
            month_month = int(date_created[5:7])
            month_verbose = f'{calendar.month_abbr[month_month]} {month_year}'

            for obj in output:
                if obj['month'] == month_verbose:
                    obj['total_count'] = obj['total_count'] + 1
                    if quotable == 'Yes':
                        obj['total_quotable_count'] = obj['total_quotable_count'] + 1
                    for lt in obj['lead_counts']:
                        if lt['lead_type'] == lead_type:
                            lt['value'] = lt['value'] + 1
                            if quotable == 'Yes':
                                lt['quotable_count'] = lt['quotable_count'] + 1
                        
                            break
                    
                    else:
                        if quotable == 'Yes':
                            initial_quotable_value = 1
                        else:
                            initial_quotable_value = 0
                        obj['lead_counts'].append({
                            'lead_type': lead_type,
                            'value': 1,
                            'quotable_count': initial_quotable_value
                        })

                    break
            
            else:
                if quotable == 'Yes':
                    initial_quotable_value = 1
                else:
                    initial_quotable_value = 0

                new_month_object = {
                    'month': month_verbose,
                    'lead_counts': [],
                    'total_count': 1,
                    'total_quotable_count': initial_quotable_value,
                    'month_month': month_month,
                    'month_year': month_year,
                }

                new_month_object['lead_counts'].append({
                    'lead_type': lead_type,
                    'value': 1,
                    'quotable_count': initial_quotable_value
                })

                output.append(new_month_object)

        return output
    else:
        print(f'No lead data for account_id {account_id}')
        return None