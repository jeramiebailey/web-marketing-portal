from docker_drf_backend.taskapp.celery import app
from celery import shared_task
from docker_drf_backend.users.models import User, UserOrgRole
from reporting.models import MonthlyReport
from reporting.utils import scrape_ahrefs_screenshots
from content_management.models import PlanningYearMonth
from docker_drf_backend.utils import send_basic_slack_message, send_custom_slack_message, send_email
from presentations.models import SlideDeckTemplate, SlideTemplate, SlideDeck, Slide
from guardian.shortcuts import assign_perm, remove_perm
from dateutil.relativedelta import *
import datetime
from django.conf import settings
from django.db.models import Q

@shared_task(name="scheduled_create_monthly_reports")
def scheduled_create_monthly_reports(pull_data=True, dry=False):
    today = datetime.datetime.today()
    today_day = today.day

    try:
        current_planning_month = PlanningYearMonth.objects.get(month=today.month, year=today.year)
    except:
        current_planning_month = None

    if today_day == 1:
        if current_planning_month:
            created_reports = current_planning_month.create_monthly_reports(dry=dry)

            if created_reports:
                if pull_data:
                    pull_current_month_report_data.delay()
                return created_reports

@shared_task(name="scheduled_validate_created_report_status")
def scheduled_validate_created_report_status():
    today = datetime.datetime.today()
    today_day = today.day

    try:
        current_planning_month = PlanningYearMonth.objects.get(month=today.month, year=today.year)
    except:
        current_planning_month = None

    if today_day == 1:
        if current_planning_month:
            created_reports = MonthlyReport.objects.filter(month=current_planning_month)
            if created_reports:
                report_status = check_month_report_data_status(month=current_planning_month.month, year=current_planning_month.year)

@shared_task(name="scheduled_create_monthly_report_presentations")
def scheduled_create_monthly_report_presentations():
    today = datetime.datetime.today()
    today_day = today.day

    try:
        current_planning_month = PlanningYearMonth.objects.get(month=today.month, year=today.year)
    except:
        current_planning_month = None

    if today_day == 1:
        if current_planning_month:
            created_reports = MonthlyReport.objects.filter(month=current_planning_month)
            if created_reports:
                for report in created_reports:
                    report.create_monthly_report_presentation()

@shared_task(name="scheduled_query_unsent_reports")
def scheduled_query_unsent_reports():
    today = datetime.datetime.today()
    today_day = today.day

    try:
        current_planning_month = PlanningYearMonth.objects.get(month=today.month, year=today.year)
    except:
        current_planning_month = None

    if today_day == 6:
        if current_planning_month:
            query_unsent_reports()

@shared_task(name="pull_month_report_data")
def pull_current_month_report_data(month=None, year=None, dry=False, only_pending=True, only_screenshots=False):
    today = datetime.datetime.today()
    today_day = today.day

    if month and year:
        try:
            current_planning_month = PlanningYearMonth.objects.get(month=month, year=year)
        except:
            current_planning_month = None
    else:
        try:
            current_planning_month = PlanningYearMonth.objects.get(month=today.month, year=today.year)
        except:
            current_planning_month = None

    if current_planning_month:
        if only_screenshots:
            corresponding_reports = MonthlyReport.objects.filter(
                Q(referring_domains_screenshot__exact='') |
                Q(referring_pages_screenshot__exact='') |
                Q(organic_keywords_screenshot__exact='') |
                Q(detailed_organic_keywords_screenshot__exact=''),
                month=current_planning_month)
            print(f'was SCREENSHOTS_ONLY, corresponding_reports count was: {corresponding_reports.count()}')
        elif only_pending:
            corresponding_reports = MonthlyReport.objects.filter(
                Q(google_analytics_data__isnull=True) | 
                Q(what_converts_data__isnull=True) |
                Q(referring_domains_screenshot__exact='') |
                Q(referring_pages_screenshot__exact='') |
                Q(organic_keywords_screenshot__exact='') |
                Q(detailed_organic_keywords_screenshot__exact=''),
                month=current_planning_month)
            print(f'was ONLY_PENDING, corresponding_reports count was: {corresponding_reports.count()}')
        else:
            corresponding_reports = MonthlyReport.objects.filter(month=current_planning_month)
            print(f'was ALL, corresponding_reports count was: {corresponding_reports.count()}')
            
        corresponding_reports_organization_urls = list(corresponding_reports.values_list('organization__domain', flat=True).distinct())

        if corresponding_reports and corresponding_reports[0]:
            for report in corresponding_reports:
                try:
                    report.pull_all_report_data()
                except:
                    print('error pulling GA/WC Data')
                    pass

        if corresponding_reports_organization_urls:
            pull_ahrefs_screenshots = scrape_ahrefs_screenshots.delay(
                account_urls=corresponding_reports_organization_urls, 
                month=current_planning_month.month, 
                year=current_planning_month.year
            )


@shared_task(name="check_month_report_data_status")
def check_month_report_data_status(month=None, year=None, send_slack_notification=True, send_email_notification=True, debug_mode=False):
    today = datetime.datetime.today()
    today_day = today.day

    if month and year:
        try:
            current_planning_month = PlanningYearMonth.objects.get(month=month, year=year)
        except:
            current_planning_month = None
    else:
        try:
            current_planning_month = PlanningYearMonth.objects.get(month=today.month, year=today.year)
        except:
            current_planning_month = None

    if current_planning_month:
        corresponding_reports = MonthlyReport.objects.filter(month=current_planning_month, organization__is_active=True, organization__report_required=True)
        if corresponding_reports and corresponding_reports[0]:
            if debug_mode or settings.DEBUG == True:
                slack_recipients = '@anthony'
            else:
                slack_recipients = '@channel'
            errors = []
            misc_errors = []
            for report in corresponding_reports:
                report_errors = {}
                missing_required_data = []
                missing_pull_data = []
                org_ga_id = report.organization.google_analytics_id
                org_wc_account = report.organization.what_converts_account
                should_repull_ahrefs = False
                
                if org_ga_id:
                    if not report.google_analytics_data:
                        missing_pull_data.append('Google Analytics Data')
                        try:
                            report.get_google_analytics_data()
                        except:
                            misc_errors.append({
                                'organization': report.organization.dba_name,
                                'error': 'failed to repull GA Data'
                            })
                else:
                    missing_required_data.append('Google Analytics ID')
                
                if org_wc_account and org_wc_account.account_id:
                    if not report.what_converts_data:
                        missing_pull_data.append('WhatConverts Data')

                        try:
                            report.get_what_converts_data()
                        except:
                            misc_errors.append({
                                'organization': report.organization.dba_name,
                                'error': 'failed to repull WC Data'
                            })
                else:
                    missing_required_data.append('WhatConverts Account Data')

                if not report.referring_domains_screenshot:
                    missing_pull_data.append('Referring Domains Screenshot')
                    should_repull_ahrefs = True
                if not report.referring_pages_screenshot:
                    missing_pull_data.append('Referring Pages Screenshot')
                    should_repull_ahrefs = True
                if not report.organic_keywords_screenshot:
                    missing_pull_data.append('Organic Keywords Screenshot')
                    should_repull_ahrefs = True
                if not report.detailed_organic_keywords_screenshot:
                    missing_pull_data.append('Detailed Organic Keywords Screenshot')
                    should_repull_ahrefs = True

                if should_repull_ahrefs:
                    try:
                        if report.organization.domain:
                            report.get_ahrefs_screenshots(delay_method=True)
                    except:
                        misc_errors.append({
                            'organization': report.organization.dba_name,
                            'error': 'failed to repull Ahrefs Data'
                        })
                
                if missing_required_data or missing_pull_data:
                    report_errors['id'] = report.id
                    report_errors['organization'] = report.organization.dba_name
                    report_errors['month'] = report.month.month
                    report_errors['year'] = report.month.year
                    report_errors['missing_required_data'] = missing_required_data
                    if org_wc_account and org_ga_id:
                        report_errors['missing_pull_data'] = missing_pull_data
                    errors.append(report_errors)

            slack_block_output = {
                'blocks': [
                    {
                        'type': "section",
                        'text': {
                            'type': "mrkdwn",
                            'text': f"\n {slack_recipients}  \n:exclamation:  *There were errors found while pulling report data for {current_planning_month.get_year_month_verbose()}*\n"
                        }
                    },
                    {
                        'type': "divider"
                    }
                ]
            }
            for error in errors:
                missing_required_data_output = ''
                missing_pull_data_output = ''

                if error['missing_required_data'] or error['missing_pull_data']:
                    try:
                        if error['missing_required_data']:
                            missing_required_data_length = len(error['missing_required_data'])
                            for required_error in error['missing_required_data']:
                                required_error_index = error['missing_required_data'].index(required_error)
                                if required_error_index != missing_required_data_length - 1:
                                    missing_required_data_output += f'> {required_error} \n'
                                else:
                                    missing_required_data_output += f'> {required_error}'
 
                    except:
                        pass
                    try:
                        if error['missing_pull_data']:
                            missing_pull_data_length = len(error['missing_pull_data'])
                            for pull_error in error['missing_pull_data']:
                                pull_error_index = error['missing_pull_data'].index(pull_error)
                                if pull_error_index != missing_pull_data_length - 1:
                                    missing_pull_data_output += f'> {pull_error} \n'
                                else:
                                    missing_pull_data_output += f'> {pull_error}'
   
                    except:
                        pass
                
                error_block = {
                    'type': "section",
                    'text': {
                        'type': 'mrkdwn',
                        'text': f':small_red_triangle:  *{error["organization"]}* had the following errors: \n',
                    }
                }
 
                if missing_required_data_output:
                    error_block_required_data = f'\n>*Missing Required Data:* \n{missing_required_data_output}'
                    error_block['text']['text'] += error_block_required_data
                if missing_pull_data_output:
                    error_block_pull_data = f'\n>*Missing Pull Data:* \n{missing_pull_data_output}'
                    error_block['text']['text'] += error_block_pull_data
                error_block['text']['text'] += '\n'
                
                slack_block_output['blocks'].append(error_block)

            if send_slack_notification:
                try:
                    slack_message = send_custom_slack_message(slack_block_output)
                except:
                    print('error_block is: ', slack_block_output)
            if send_email_notification:
                recipients = ['support@321webmarketing.com',]
                staff_members = User.objects.filter(is_active=True, is_staff=True)
                # for staff in staff_members:
                #     recipients.append(staff.email)
                email_notification = send_email(
                    template='reporting/report_data_status_notification.html',
                    recipients=recipients,
                    subject=f'Errors found while pulling report data for {current_planning_month.get_year_month_verbose()}',
                    context={
                        'errors': errors,
                        'misc_errors': misc_errors,
                        'planning_month': current_planning_month
                    },
                    debug=debug_mode
                )
            print(f'misc_errors are: {misc_errors}')
            return errors

@shared_task(name="query_unsent_reports")
def query_unsent_reports(month=None, year=None, send_slack_notification=True, send_email_notification=True, debug_mode=False):
    today = datetime.datetime.today()
    today_day = today.day

    if month and year:
        try:
            target_planning_month = PlanningYearMonth.objects.get(month=month, year=year)
        except:
            target_planning_month = None
    else:
        try:
            target_planning_month = PlanningYearMonth.objects.get(month=today.month, year=today.year)
        except:
            target_planning_month = None

    if target_planning_month:
        corresponding_reports = MonthlyReport.objects.filter(month=target_planning_month, organization__is_active=True, organization__report_required=True)
        if corresponding_reports and corresponding_reports[0]:
            unsent_reports = corresponding_reports.filter(email_entries__isnull=True)

            if unsent_reports:
                if send_slack_notification:
                    if debug_mode or settings.DEBUG == True:
                        slack_recipients = '@anthony'
                    else:
                        slack_recipients = '@channel'

                    slack_unsent_report_output = ''

                    for report in unsent_reports:
                        slack_unsent_report_output += f'\n> {report.organization.dba_name}'

                    slack_block_output = {
                        'blocks': [
                            {
                                'type': "section",
                                'text': {
                                    'type': "mrkdwn",
                                    'text': f"\n {slack_recipients}  \n:exclamation:  *Unsent Report Notifications for {target_planning_month.get_year_month_verbose()}*\n"
                                }
                            },
                            {
                                'type': "divider"
                            },
                            {
                                'type': "section",
                                'text': {
                                    'type': 'mrkdwn',
                                    'text': f':small_red_triangle: The following organizations were not sent a report: \n {slack_unsent_report_output}',
                                }
                            }
                        ]
                    }

                    slack_message = send_custom_slack_message(slack_block_output)

                if send_email_notification:
                    recipients = ['support@321webmarketing.com',]
                    email_notification = send_email(
                        template='reporting/unsent_reports_notification.html',
                        recipients=recipients,
                        subject=f'Unsent Report Notifications for {target_planning_month.get_year_month_verbose()}',
                        context={
                            'unsent_reports': unsent_reports,
                            'planning_month': target_planning_month
                        },
                        debug=debug_mode
                    )

            if slack_message:
                sent_slack_message = True
            else:
                sent_slack_message = False

            print('email_notification is: ', email_notification)
            if email_notification:
                sent_email_notification = True
            else:
                sent_email_notification = False

            data = {
                'unsent_reports': unsent_reports,
                'sent_slack_message': sent_slack_message,
                'sent_email_notification': sent_email_notification
            }

            return data

@app.task
def assign_report_permissions(user_id):
    
    try:
        user = User.objects.get(id=user_id)
        print('assign_report_permissions found user as : ', user)
    except:
        user = None

    if user:
        user_org_roles = UserOrgRole.objects.prefetch_related('user', 'organization', 'role').filter(user=user)
        print('assign_report_permissions found user_org_roles as : ', user_org_roles)
        if user_org_roles:
            for role in user_org_roles:
                corresponding_organization = role.organization
                if corresponding_organization:
                    corresponding_organization_reports = corresponding_organization.org_monthly_reports.all()
                    assign_perm('view_monthlyreport', user, corresponding_organization_reports)
                    print('assign_report_permissions should of assigned perms here')
                    for report in corresponding_organization_reports:
                        report_presentation = report.presentation
                        if report_presentation:
                            report_presentation_slides = report_presentation.slides.all()
                            assign_perm('view_slidedeck', user, report_presentation)
                            for slide in report_presentation_slides:
                                assign_perm('view_slide', user, slide)
