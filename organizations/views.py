from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import mixins, status, viewsets, permissions
from .models import WhatConvertsAccount, Organization
from .serializers import WhatConvertsAccountSerializer
from api.utils import get_report_data, get_whatconverts_data, get_ga4_report_data
from organizations.serializers import OrganizationSerializer, DetailedOrganizationSerializer
from rest_framework.decorators import action
from presentations.models import SlideDeckTemplate
from presentations.serializers import SlideDeckTemplateSerializer
from rest_framework.parsers import FileUploadParser, MultiPartParser, FormParser, JSONParser
from rest_framework_guardian import filters
from api.permissions import CustomObjectPermissions
from django.apps import apps
from content_management.serializers import BriefContentArticleSerializer

class WhatConvertsAccountViewSet(viewsets.ModelViewSet):
    queryset = WhatConvertsAccount.objects.all()
    serializer_class = WhatConvertsAccountSerializer

class OrganizationViewSet(viewsets.ModelViewSet):
    parser_classes = (MultiPartParser, FormParser,)
    queryset = Organization.objects.select_related('account_lead', 'project_manager').prefetch_related(
        'user_default_organization', 
        'organization_requirements',
        ).filter(is_active=True).order_by('dba_name')
    permission_classes = (CustomObjectPermissions,)
    serializer_class = OrganizationSerializer
    filter_backends = (filters.DjangoObjectPermissionsFilter,) 

    def get_queryset(self):
        queryset = super(OrganizationViewSet, self).get_queryset()
        archiving = self.request.query_params.get('archive', None)
 
        if archiving:
            queryset = Organization.objects.select_related('account_lead', 'project_manager').prefetch_related(
                'user_default_organization', 
                'organization_requirements',
                ).all().order_by('dba_name')

        return queryset
    

    def perform_create(self, serializer):
        instance = super(OrganizationViewSet, self).perform_create(serializer)
        what_converts_account = self.request.data.get('what_converts_account')
        logo = self.request.data.get('logo')
        if what_converts_account is not None:
            serializer.save(what_converts_account=what_converts_account, logo=logo)
        else:
            serializer.save(logo=logo)

    def perform_update(self, serializer):
        instance = super(OrganizationViewSet, self).perform_update(serializer)
        obj = self.get_object()
        what_converts_account = self.request.data.get('what_converts_account')
        logo = self.request.data.get('logo')
        if what_converts_account is None:
            what_converts_account = obj.what_converts_account
        if logo is None:
            logo = obj.logo

        serializer.save(what_converts_account=what_converts_account, logo=logo)

    def get_serializer_class(self):
        detailed = self.request.query_params.get('detailed', None)

        if detailed:
            return DetailedOrganizationSerializer
        else:
            return OrganizationSerializer

    @action(detail=True, methods=['get'])
    def get_pending_content_approvals(self, request, pk=None):
        instance = self.get_object()
        if request.user.has_perm('organizations.view_organization') or self.request.user.is_staff:
            pending_content_approvals = instance.get_pending_content_approvals()
            response = BriefContentArticleSerializer(pending_content_approvals, many=True)
    
            return Response(response.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def get_google_analytics_report(self, request, pk=None):
        instance = self.get_object()

        if request.user.has_perm('reporting.view_organization') or self.request.user.is_staff:
            months_back_query = self.request.query_params.get('monthsBack', None)
            try:
                months_back_query = int(months_back_query)
            except:
                months_back_query = None

            if instance.google_analytics_id and months_back_query and isinstance(months_back_query, int):
                report = get_report_data(view_id=instance.google_analytics_id, months_back=months_back_query)
            else:
                report = get_report_data(view_id=instance.google_analytics_id)

            if not report:
                if instance.google_analytics_id and months_back_query and isinstance(months_back_query, int):
                        report = get_ga4_report_data(property_id=instance.google_analytics_id, months_back=months_back_query)
                else:
                    report = get_ga4_report_data(property_id=instance.google_analytics_id)

            if report:
                return Response(report, status=status.HTTP_200_OK)
            else:
                return Response(
                    data={'error': 'Unable to get report'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        else:
            return Response('You are Unauthorized to make this action.', status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=True, methods=['get'])
    def get_what_converts_report(self, request, pk=None):
        instance = self.get_object()

        if request.user.has_perm('reporting.view_organization') or self.request.user.is_staff:
            months_back_query = self.request.query_params.get('monthsBack', None)
            try:
                months_back_query = int(months_back_query)
            except:
                months_back_query = None

            if instance.what_converts_account and months_back_query and isinstance(months_back_query, int):
                report = get_whatconverts_data(account_id=instance.what_converts_account.account_id, months_back=months_back_query)
            else:
                report = get_whatconverts_data(account_id=instance.what_converts_account.account_id)

            if report:
                return Response(report, status=status.HTTP_200_OK)
            else:
                return Response(
                    data={'error': 'Unable to get report'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        else:
            return Response('You are Unauthorized to make this action.', status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=True, methods=['post'])
    def create_report_template_from_master(self, request, pk=None):
        instance = self.get_object()
        ContentTypeModel= apps.get_model(app_label='contenttypes', model_name='ContentType')
        organization_content_type = ContentTypeModel.objects.get_for_model(Organization)
        print(f'organization_content_type is: {organization_content_type}')
        if request.user.has_perm('reporting.update_monthlyreport') or self.request.user.is_staff:
            try:
                master_org_report_template = SlideDeckTemplate.objects.get(content_type=organization_content_type, is_master_template=True)
            except:
                master_org_report_template = None

            if master_org_report_template:
                new_report_template = instance.create_report_template_from_master()
                response = SlideDeckTemplateSerializer(new_report_template)
                
                return Response(response.data, status=status.HTTP_200_OK)
            else:
                return Response(
                    data={'error': 'Master Report Template not found'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        else:
            return Response('You are Unauthorized to make this action.', status=status.HTTP_401_UNAUTHORIZED)

    @action(methods=['post'], detail=True)
    def create_wc_account(self, request, pk):
        if request.user.has_perm('content_management.create_organization') or self.request.user.is_staff:
            obj = self.get_object()
            account_id = request.data.get('account_id', None)
            report_calls = request.data.get('report_calls', None)
            report_form_fills = request.data.get('report_form_fills', None)
            report_chats = request.data.get('report_chats', None)
            spt_account = request.data.get('spt_account', None)

            if account_id is None:
                return Response(
                    data={'error': 'Account ID Required'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                new_wc_account = obj.create_whatconverts_account(
                    account_id=account_id,
                    report_calls=report_calls,
                    report_form_fills=report_form_fills,
                    report_chats=report_chats,
                    spt_account=spt_account,
                )

                if new_wc_account is True:
                    updated_organization = Organization.objects.get(pk=obj.pk)
                    response = OrganizationSerializer(updated_organization)
                    return Response(response.data, status=status.HTTP_200_OK)
                
                else:
                    return Response(
                        data={'errors': new_wc_account},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
        else:
            return Response('You are Unauthorized to make this action.', status=status.HTTP_401_UNAUTHORIZED)

