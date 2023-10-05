from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.http import HttpResponseRedirect
from rest_framework.views import APIView
from rest_framework.response import Response
from django.urls import reverse
from rest_framework.permissions import IsAuthenticated
from rest_framework import mixins, status, viewsets, permissions
from .models import MonthlyReport, ReportEmailEntry
from organizations.models import Organization
from organizations.serializers import OrganizationSerializer
from presentations.serializers import SlideDeckTemplateSerializer
from .serializers import MonthlyReportSerializer, MonthlyReportActionsSerializer, MonthlyReportTemplateSerializer, ReportEmailEntrySerializer
from reporting.tasks import pull_current_month_report_data, check_month_report_data_status, query_unsent_reports
from content_management.models import PlanningYearMonth
from presentations.models import SlideDeck
from django.core.mail import send_mail
import environ
from rest_framework.decorators import action
from django.template.loader import render_to_string
from docker_drf_backend.users.models import UserOrgRole
from rest_framework_guardian import filters
from api.permissions import CustomObjectPermissions
from guardian.shortcuts import get_objects_for_user, get_perms
from django.conf import settings
import calendar

frontend_url = settings.FRONTEND_URL 

class ReportEmailEntryViewSet(viewsets.ModelViewSet):
    queryset = ReportEmailEntry.objects.prefetch_related('report').all()
    serializer_class = ReportEmailEntrySerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = super(ReportEmailEntryViewSet, self).get_queryset()

        report_id = self.request.query_params.get('report', None)
    
        if report_id is not None:
            try:
                report = MonthlyReport.objects.get(id=report_id)
            except:
                report = None
            
            if report:
                queryset = queryset.filter(report=report)

                return queryset

        return queryset

    @action(detail=True, methods=['post'])
    def confirm_viewed(self, request, pk=None):
        email_entry = self.get_object()
        report = email_entry.report
        requesting_user = request.user
        email_entry_user = email_entry.get_user()

        if email_entry_user:
            if email_entry_user.id == requesting_user.id:
                if not email_entry.link_clicked:
                    email_entry.link_clicked = True
                    updated_email_entry = email_entry.save()
                    response = ReportEmailEntrySerializer(updated_email_entry)
                    return Response(response.data, status=status.HTTP_200_OK)
                else:
                    return Response('Entry has already been marked as viewed', status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response('You are not authorized to make this request', status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"Email Entry User Not Found"}, status=status.HTTP_404_NOT_FOUND)


class MonthlyReportViewSet(viewsets.ModelViewSet):
    queryset = MonthlyReport.objects.prefetch_related('organization', 'month', 'creator', 'approver').filter(organization__report_required=True, month__isnull=False).order_by('-date_created')
    serializer_class = MonthlyReportSerializer
    permission_classes = (CustomObjectPermissions,)
    filter_backends = (filters.DjangoObjectPermissionsFilter,)

    def get_queryset(self):
        queryset = MonthlyReport.objects.prefetch_related('organization', 'month', 'creator', 'approver').filter(organization__report_required=True, month__isnull=False).order_by('-date_created')

        month = self.request.query_params.get('month', None)
        if month is not None:
            try:
                planning_year_month = PlanningYearMonth.objects.get(id=month)
            except:
                planning_year_month = None
            
            if planning_year_month:
                queryset = queryset.filter(month=month)

                return queryset

        return queryset

    
    @action(detail=True, methods=['post'])
    def pull_ga_data(self, request, pk=None):
        report = self.get_object()
        if request.user.has_perm('reporting.update_monthlyreport') or self.request.user.is_staff:
            if report.organization.google_analytics_id:
                try:
                    ga_data = report.get_google_analytics_data()
                except:
                    ga_data = None
                
                if ga_data is not None:
                    new_report_data = MonthlyReport.objects.get(pk=report.pk)
                    response = MonthlyReportSerializer(new_report_data)
                    return Response(response.data, status=status.HTTP_200_OK)

                else:
                    return Response('Google Analytics data failed to pull. This is most likely due to permissions on the GA Account.',
                                        status=status.HTTP_400_BAD_REQUEST)

            else:
                return Response('Organization does not have a valid Google Analytics ID. Please first add one.',
                                        status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response('You are not authorized to make this request',
                            status=status.HTTP_401_UNAUTHORIZED)

    
    @action(detail=True, methods=['post'])
    def pull_wc_data(self, request, pk=None):
        report = self.get_object()
        if request.user.has_perm('reporting.update_monthlyreport') or self.request.user.is_staff:
            if report.organization.what_converts_account:
                try:
                    wc_data = report.get_what_converts_data()
                except:
                    wc_data = None
                
                if wc_data is not None:
                    new_report_data = MonthlyReport.objects.get(pk=report.pk)
                    response = MonthlyReportSerializer(new_report_data)
                    return Response(response.data, status=status.HTTP_200_OK)
                    
                else:
                    return Response('What Converts data failed to pull',
                                    status=status.HTTP_400_BAD_REQUEST)
            
            else:
                return Response('Organization does not have a valid WhatConverts Account. Please first add one.',
                                    status=status.HTTP_400_BAD_REQUEST)
        
        else:
            return Response('You are not authorized to make this request',
                            status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=True, methods=['post'])
    def pull_ahrefs_data(self, request, pk=None):
        print('pull_ahrefs_data fired')
        report = self.get_object()
        if request.user.has_perm('reporting.update_monthlyreport') or self.request.user.is_staff:
            if report.organization.domain:
                ahrefs_screenshots = report.get_ahrefs_screenshots()
                
                if ahrefs_screenshots:
                    new_report_data = MonthlyReport.objects.get(pk=report.pk)
                    response = MonthlyReportSerializer(new_report_data)
                    return Response(response.data, status=status.HTTP_200_OK)
                    
                else:
                    return Response('Ahrefs Scraper failed to execute. This is most likely due to the domain not being valid.',
                                    status=status.HTTP_400_BAD_REQUEST)
            
            else:
                return Response('Organization does not have a domain yet. Please first add one.',
                                    status=status.HTTP_400_BAD_REQUEST)
        
        else:
            return Response('You are not authorized to make this request',
                            status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=True, methods=['post'])
    def pull_report_data(self, request, pk=None):
        report = self.get_object()
        if request.user.has_perm('reporting.update_monthlyreport') or self.request.user.is_staff:
            try:
                report_data = report.pull_all_report_data
            except:
                report_data = None
            if report_data:
                new_report_data = MonthlyReport.objects.get(pk=report.pk)
                response = MonthlyReportSerializer(new_report_data)
                return Response(response.data, status=status.HTTP_200_OK)
            else:
                return Response('Error pulling report data.',
                                    status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response('You are not authorized to make this request',
                            status=status.HTTP_401_UNAUTHORIZED)
    
    @action(detail=True, methods=['post'])
    def create_report_presentation(self, request, pk=None):
        report = self.get_object()
        if request.user.has_perm('reporting.update_monthlyreport') or self.request.user.is_staff:
            if report.organization.monthly_report_template:
                if not report.presentation:
                    report.create_monthly_report_presentation()
                    new_report_data = MonthlyReport.objects.get(pk=report.pk)
                    response = MonthlyReportSerializer(new_report_data)
                    return Response(response.data, status=status.HTTP_200_OK)
                else:
                    return Response('A report presentation has already been created for this month.',
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response('Report has no associated organization template',
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response('You are not authorized to make this request',
                            status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=True, methods=['post'])
    def recreate_report_presentation(self, request, pk=None):
        report = self.get_object()
        if report:
            if report.organization.monthly_report_template:
                if not report.presentation:
                    return Response('No existing report template.',
                                status=status.HTTP_400_BAD_REQUEST)
                else:
                    old_presentation = report.presentation
                    old_presentation.delete()

                    new_presentation = report.create_monthly_report_presentation()
                    new_report_data = MonthlyReport.objects.get(pk=report.pk)
                    response = MonthlyReportSerializer(new_report_data)
                    return Response(response.data, status=status.HTTP_200_OK)
            else:
                return Response('Report has no associated organization template',
                                status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def send_report(self, request, pk=None):
        report = self.get_object()
        if request.user.has_perm('reporting.update_monthlyreport') or self.request.user.is_staff:
            test_email = self.request.query_params.get('test', None)
            debug_mode = self.request.query_params.get('debug_mode', None)
            if test_email is not None:
                is_test = True
            else:
                is_test = False
            
            if debug_mode is not None:
                is_debug = True
            else:
                is_debug = False

            if report.organization and report.organization.business_email:
                if report.status == 'finalReview' or report.status == "sent":
                    report_notification = report.send_report_notification(is_test=is_test, is_debug=is_debug)
                    response = MonthlyReportSerializer(report)
                    return Response(response.data, status=status.HTTP_200_OK)
                else:
                    return Response(f'Report is not ready to send out. The current status is {report.status}', status=status.HTTP_400_BAD_REQUEST)
                    
            else:
                return Response('Report has no associated organization',
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response('You are not authorized to make this request',
                            status=status.HTTP_401_UNAUTHORIZED)



def unsubscribe(request, uuid, email_address):
    valid_report_email_entry = get_object_or_404(ReportEmailEntry, uuid=uuid, email=email_address)
    if valid_report_email_entry:
            report_organization = valid_report_email_entry.report.organization
            corresponding_user_org_role = get_object_or_404(UserOrgRole, organization=report_organization, user__email=email_address)
            organization_name = report_organization.dba_name

            if not valid_report_email_entry.link_clicked:
                if corresponding_user_org_role:
                    corresponding_user_org_role.receive_reporting_email = False
                    corresponding_user_org_role.save()
                    valid_report_email_entry.link_clicked = True
                    valid_report_email_entry.did_unsubscribe = True
                    valid_report_email_entry.save()

                    return HttpResponseRedirect(reverse('reporting:unsubscribe-success', kwargs={
                        'email_address': email_address,
                        'organization_name': organization_name
                        }))
            else:
                return HttpResponseRedirect(reverse('reporting:unsubscribe-failure', kwargs={
                        'email_address': email_address,
                        'organization_name': organization_name
                        }))


def unsubscribe_success(request, *args, **kwargs):
    try:
        email_address = kwargs['email_address']
        organization_name = kwargs['organization_name']
    except:
        email_address = None
        organization_name = None

        raise Http404("No email address or organization name provided.")

    if email_address and organization_name:
        template = 'reporting/unsubscribe_success.html'
        context = {
            'email_address': email_address,
            'organization_name': organization_name,
        }
        return render(request, template, context)

def unsubscribe_failure(request, *args, **kwargs):
    try:
        email_address = kwargs['email_address']
        organization_name = kwargs['organization_name']
    except:
        email_address = None
        organization_name = None

        raise Http404("No email address or organization name provided.")

    if email_address and organization_name:
        template = 'reporting/unsubscribe_failure.html'
        context = {
            'email_address': email_address,
            'organization_name': organization_name,
        }
        return render(request, template, context)


class CreateMonthlyReportsView(APIView):
    serializer_class = MonthlyReportActionsSerializer

    def get(self, request, format=None):
        return Response({"message": "GET Method not available"})

    def post(self, request, format=None):
        serializer = MonthlyReportActionsSerializer(data=request.data)
        if request.user.has_perm('reporting.update_monthlyreport') or request.user.is_staff:

            if serializer.is_valid():
                planning_month = serializer.data.get('planning_month')

                if planning_month:
                    try:
                        target_planning_month = PlanningYearMonth.objects.get(id=planning_month)
                    except:
                        target_planning_month = None

                    if target_planning_month:
                        created_reports = target_planning_month.create_monthly_reports()

                        if created_reports:
                            # Trying in prod without delay
                            # pull_current_month_report_data.delay(month=target_planning_month.month, year=target_planning_month.year)
                            pull_current_month_report_data(month=target_planning_month.month, year=target_planning_month.year)

                            return Response(
                                    {
                                        "response": "Monthly Reports Created.",
                                    }, status=status.HTTP_200_OK)

                        else:
                            return Response({"response": f"There was an error creating your reports. Errors: {created_reports}"}, status=status.HTTP_400_BAD_REQUEST)

                    
                    else:
                        return Response({"response": "Planning Month Not Found"}, status=status.HTTP_404_NOT_FOUND)

                else:
                    return Response({"response": "planning_month required."}, status=status.HTTP_400_BAD_REQUEST)
            
            else:   
                return Response({"response": "Not valid", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({'Unauthorized': "You do not have permissions to do that."},
                        status=status.HTTP_401_UNAUTHORIZED)


class ValidateMonthlyReportDataView(APIView):
    serializer_class = MonthlyReportActionsSerializer

    def get(self, request, format=None):
        return Response({"message": "GET Method not available"})

    def post(self, request, format=None):
        serializer = MonthlyReportActionsSerializer(data=request.data)
        if request.user.has_perm('reporting.update_monthlyreport') or request.user.is_staff:

            if serializer.is_valid():
                planning_month = serializer.data.get('planning_month')

                if planning_month:
                    try:
                        target_planning_month = PlanningYearMonth.objects.get(id=planning_month)
                    except:
                        target_planning_month = None

                    if target_planning_month:
                        created_reports = MonthlyReport.objects.filter(month=target_planning_month)

                        if created_reports:
                            debug_mode = self.request.query_params.get('debug_mode', None)
                            
                            if debug_mode is not None:
                                is_debug = True
                            else:
                                is_debug = False

                            report_status = check_month_report_data_status(month=target_planning_month.month, year=target_planning_month.year, debug_mode=is_debug)

                            return Response(
                                    {
                                        "response": "Report Status Check Successful, Notifications Sent.",
                                        "debug_mode": is_debug,
                                    }, status=status.HTTP_200_OK)

                        else:
                            return Response({"response": f"There was an error validating your report data."}, status=status.HTTP_400_BAD_REQUEST)

                    
                    else:
                        return Response({"response": "Planning Month Not Found"}, status=status.HTTP_404_NOT_FOUND)

                else:
                    return Response({"response": "planning_month required."}, status=status.HTTP_400_BAD_REQUEST)
            
            else:   
                return Response({"response": "Not valid", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({'Unauthorized': "You do not have permissions to do that."},
                        status=status.HTTP_401_UNAUTHORIZED)

class CreateReportPresentationsView(APIView):
    serializer_class = MonthlyReportActionsSerializer

    def get(self, request, format=None):
        return Response({"message": "GET Method not available"})

    def post(self, request, format=None):
        serializer = MonthlyReportActionsSerializer(data=request.data)
        if request.user.has_perm('reporting.update_monthlyreport') or request.user.is_staff:

            if serializer.is_valid():
                planning_month = serializer.data.get('planning_month')

                if planning_month:
                    try:
                        target_planning_month = PlanningYearMonth.objects.get(id=planning_month)
                    except:
                        target_planning_month = None

                    if target_planning_month:
                        created_reports = MonthlyReport.objects.filter(month=target_planning_month)

                        if created_reports:
                            for report in created_reports:
                                report.create_monthly_report_presentation()

                            return Response(
                                    {
                                        "response": "Monthly Report Presentations Successfully Created.",
                                    }, status=status.HTTP_200_OK)

                        else:
                            return Response({"response": f"There was an error creating your monthly report presentations."}, status=status.HTTP_400_BAD_REQUEST)

                    
                    else:
                        return Response({"response": "Planning Month Not Found"}, status=status.HTTP_404_NOT_FOUND)

                else:
                    return Response({"response": "planning_month required."}, status=status.HTTP_400_BAD_REQUEST)
            
            else:   
                return Response({"response": "Not valid", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({'Unauthorized': "You do not have permissions to do that."},
                        status=status.HTTP_401_UNAUTHORIZED)

class QueryUnsentReportsView(APIView):
    serializer_class = MonthlyReportActionsSerializer

    def get(self, request, format=None):
        return Response({"message": "GET Method not available"})

    def post(self, request, format=None):
        serializer = MonthlyReportActionsSerializer(data=request.data)
        if request.user.has_perm('reporting.update_monthlyreport') or request.user.is_staff:

            if serializer.is_valid():
                planning_month = serializer.data.get('planning_month')

                if planning_month:
                    try:
                        target_planning_month = PlanningYearMonth.objects.get(id=planning_month)
                    except:
                        target_planning_month = None

                    if target_planning_month:
                        created_reports = MonthlyReport.objects.filter(month=target_planning_month)

                        if created_reports:
                            debug_mode = self.request.query_params.get('debug_mode', None)
                            
                            if debug_mode is not None:
                                is_debug = True
                            else:
                                is_debug = False

                            unsent_reports = query_unsent_reports(month=target_planning_month.month, year=target_planning_month.year, debug_mode=is_debug)

                            response = MonthlyReportSerializer(unsent_reports["unsent_reports"])
                            
                            return Response({
                                'unsent_reports': response.data,
                                'sent_slack_message': unsent_reports["sent_slack_message"],
                                'sent_email_notification': unsent_reports["sent_email_notification"]
                            }, status=status.HTTP_200_OK)

                        else:
                            return Response({"response": f"There was an error querying unsent reports."}, status=status.HTTP_400_BAD_REQUEST)

                    
                    else:
                        return Response({"response": "Planning Month Not Found"}, status=status.HTTP_404_NOT_FOUND)

                else:
                    return Response({"response": "planning_month required."}, status=status.HTTP_400_BAD_REQUEST)
            
            else:   
                return Response({"response": "Not valid", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({'Unauthorized': "You do not have permissions to do that."},
                        status=status.HTTP_401_UNAUTHORIZED)

class BulkMonthlyReportPresentationTemplateUpdateView(APIView):
    serializer_class = MonthlyReportTemplateSerializer

    def get(self, request, format=None):
        return Response({"message": "GET Method not available"})

    def post(self, request, format=None):
        serializer = MonthlyReportTemplateSerializer(data=request.data)
        if request.user.has_perm('reporting.update_monthlyreport') or request.user.is_staff:

            if serializer.is_valid():
                organizations = serializer.data.get('organizations')

                if organizations:
                    try:
                        target_organizations = Organization.objects.filter(id__in=organizations)
                    except:
                        target_organizations = None

                    if target_organizations:

                        try:
                            for org in target_organizations:
                                new_presentation_template = org.create_report_template_from_master()
                                print(f'{org.dba_name} new template ID is {new_presentation_template.id}')
                                presentation_successfully_updated = True
                        except:
                            presentation_successfully_updated = False

                        if presentation_successfully_updated:
                            output_serializer = OrganizationSerializer(target_organizations, many=True, context={'request': request})
                            return Response(output_serializer.data, status=status.HTTP_200_OK)

                        else:
                            return Response({"response": f"There was an error creating your monthly report presentations. Errors: {report_status}"}, status=status.HTTP_400_BAD_REQUEST)

                    
                    else:
                        return Response({"response": "No Organizations Found"}, status=status.HTTP_404_NOT_FOUND)

                else:
                    return Response({"response": "At least one organization required."}, status=status.HTTP_400_BAD_REQUEST)
            
            else:   
                return Response({"response": "Not valid", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({'Unauthorized': "You do not have permissions to do that."},
                        status=status.HTTP_401_UNAUTHORIZED)