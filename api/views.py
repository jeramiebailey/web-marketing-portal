from rest_framework import viewsets, permissions, mixins, status
from django.conf import settings
from docker_drf_backend.users.models import User, UserOrgRole, Preferences
from rest_framework.response import Response
from notifications.models import Notification
from . import serializers
from django.contrib.auth.models import Group, Permission
from content_management.models import PlanningYearMonth, ContentStatus, ContentType, ContentChannel, ContentKeywords, Writer, ContentArticle, ContentComments, ArticleTemplate, OrganizationRequirements, ParentKeyword, Keyword, KeywordMeta, ContentTag, UrlRanking, OrganizationEditorialRequirement, ContentProject
from allauth.account import app_settings as allauth_settings
from rest_auth.app_settings import (TokenSerializer,
                                    JWTSerializer,
                                    create_token)
from rest_auth.registration.views import RegisterView
from invitations.app_settings import app_settings as invitations_settings
from rest_invitations.views import accept_invitation
from rest_invitations.app_settings import (CREATE_AND_SEND_URL, SEND_MULTIPLE_URL, SEND_URL,
                           InvitationBulkWriteSerializer, InvitationModel,
                           InvitationReadSerializer, InvitationWriteSerializer)
from invitations.adapters import get_invitations_adapter

from invitations.signals import invite_accepted
from rest_framework.views import APIView
from rest_framework.decorators import (api_view, detail_route, list_route,
                                       permission_classes)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_guardian import filters
from api.permissions import CustomObjectPermissions
from guardian.shortcuts import get_objects_for_user, get_perms
from organizations.models import Organization
from rest_framework.decorators import (api_view, detail_route, list_route,
                                       permission_classes)
from django.contrib.auth.models import Group
from organizations.models import Organization
from allauth.account.utils import complete_signup
from .serializers import *
from django.db.models import Prefetch
from .utils import search_drive_files, create_drive_file
from googleapiclient.discovery import build
from django.template.loader import render_to_string
from guardian.shortcuts import assign_perm, remove_perm
import environ
from django.db.models import Q
from rest_framework.decorators import action
from django.core.mail import send_mail
from django.db import transaction
from rest_framework.pagination import PageNumberPagination
from django.contrib.contenttypes.models import ContentType as ContentObjectType
from api.parsers import MultipartJsonParser
from .constants import ALLOWED_MODEL_TYPES, ALLOWED_APP_LABELS
from rest_framework.parsers import FileUploadParser, MultiPartParser, FormParser, JSONParser
from django.apps import apps
from docker_drf_backend.users.serializers import QuickUserDetailsSerializer, BriefUserDetailsSerializer, UserDetailsSerializer
from docker_drf_backend.utils import send_email
# from django.utils.decorators import method_decorator
# from django.views.decorators.cache import cache_page

env = environ.Env()

google_api_key = env('GOOGLE_API_KEY')
mailgun_api_key = env('MAILGUN_API_KEY')
mailgun_domain = 'mg.321webmarketing.com'

def current_year():
    return datetime.date.today().year

def current_month():
    return datetime.date.today().month

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'page_size'
    max_page_size = 100

class ContentObjectTypeViewSet(viewsets.ModelViewSet):
    queryset = ContentObjectType.objects.all()
    serializer_class = ContentObjectTypeSerializer

    def get_queryset(self):
        queryset = ContentObjectType.objects.filter(model__in=ALLOWED_MODEL_TYPES)
        return queryset



class ContentStaffViewSet(viewsets.ModelViewSet):
    queryset = User.objects.select_related('default_role').prefetch_related(
            'user_preferences', 'org_roles', 'groups', 'writer', 'user_preferences__default_organization').filter(is_staff=True, is_active=True)
    permission_classes = (CustomObjectPermissions,)
    serializer_class = BriefUserDetailsSerializer
    filter_backends = (filters.DjangoObjectPermissionsFilter,)

    def get_queryset(self):
        queryset = User.objects.select_related('default_role').prefetch_related(
            'user_preferences', 'org_roles', 'groups', 'writer', 'user_preferences__default_organization').filter(
                Q(is_staff=True) |
                Q(groups__name__in=['Editor']) |
                Q(groups__name__in=['Contractor']),
                is_active=True
                ).distinct()

        org_id = self.request.query_params.get('client', None)

        if org_id:
            try:
                organization = Organization.objects.get(id=org_id)
            except:
                organization = None
            
            queryset = User.objects.select_related('default_role').prefetch_related(
                'user_preferences', 
                'org_roles', 
                'groups', 
                'writer', 
                'user_preferences__default_organization'
                )
            queryset = queryset.filter(
                Q(org_roles__role=Group.objects.get(name="Customer")) | 
                Q(org_roles__role=Group.objects.get(name="Account Owner")) |
                Q(org_roles__role=Group.objects.get(name="Contractor")) | 
                Q(org_roles__role=Group.objects.get(name="Editor")), 
                Q(org_roles__organization=organization) |
                Q(org_roles__organization__dba_name='321 Web Marketing'),
                is_active=True
                ).distinct()

        return queryset


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    permission_classes = (CustomObjectPermissions,)
    serializer_class = NotificationSerializer
    filter_backends = (filters.DjangoObjectPermissionsFilter,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    permission_classes = (CustomObjectPermissions,)
    serializer_class = AddressSerializer
    filter_backends = (filters.DjangoObjectPermissionsFilter,)


class PlanningYearMonthViewSet(viewsets.ModelViewSet):
    queryset = PlanningYearMonth.objects.all().order_by('-year', '-month')
    serializer_class = PlanningYearMonthSerializer
    permission_classes = [permissions.IsAuthenticated,]
    # pagination_class = StandardResultsSetPagination
    # filter_backends = (filters.DjangoObjectPermissionsFilter,)

    def get_serializer_class(self):
        brief = self.request.query_params.get('brief', None)

        if brief:
            return BriefPlanningYearMonthSerializer
        else:
            return PlanningYearMonthSerializer

    def get_queryset(self):
        queryset = super(PlanningYearMonthViewSet, self).get_queryset()
        year = self.request.query_params.get('year', None)
        month = self.request.query_params.get('month', None)
        additional = self.request.query_params.get('additional', None)

        if year is not None and month is not None:
            queryset = queryset.filter(year=year, month=month)

        elif not self.action == 'retrieve':
            if additional is not None and additional.isnumeric():
                try:
                    queryset = queryset.order_by('-year', '-month')[9:int(additional) + 8]
                except:
                    print(f'there was an error parsing additional, additional evaled to: {additional}')
                    queryset = queryset.order_by('-year', '-month')[9:]
            else:
                queryset = queryset.order_by('-year', '-month')[:8]

        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        return queryset

    @action(detail=True, methods=['post'])
    def generate_monthly_reports(self, request, pk=None):
        if request.user.has_perm('content_management.delete_planningmonth') or self.request.user.is_staff:
            obj = self.get_object()
            try:
                created_reports = obj.create_monthly_reports()
            except:
                created_reports = False

            if created_reports:
                return Response(created_reports, status=status.HTTP_200_OK)
            else:
                return Response('Error creating reports',
                                    status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response('You are Unauthorized to make this action.', status=status.HTTP_401_UNAUTHORIZED)
    
    # @method_decorator(cache_page(60*5))
    # def dispatch(self, *args, **kwargs):
    #     return super(PlanningYearMonthViewSet, self).dispatch(*args, **kwargs)


class ContentProjectViewSet(viewsets.ModelViewSet):
    queryset = ContentProject.objects.all().order_by('due_date')
    serializer_class = ContentProjectSerializer
    permission_classes = [permissions.IsAuthenticated,]

    def get_queryset(self):
        queryset = ContentProject.objects.all().filter(complete=False).order_by('due_date')
        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        return queryset
    
class ContentStatusViewSet(viewsets.ModelViewSet):
    queryset = ContentStatus.objects.all().prefetch_related(
        'contentStatus', 
        'contentStatus__project', 
        'contentStatus__planning_year_month'
        ).order_by('order')
    serializer_class = ContentStatusSerializer
     # Not currently restricting Content Statuses from view
    permission_classes = [permissions.IsAuthenticated,]
    # filter_backends = (filters.DjangoObjectPermissionsFilter,)

    # @method_decorator(cache_page(60*5))
    def dispatch(self, *args, **kwargs):
        return super(ContentStatusViewSet, self).dispatch(*args, **kwargs)
    
class ContentTypeViewSet(viewsets.ModelViewSet):
    queryset = ContentType.objects.all()
    serializer_class = ContentTypeSerializer
    permission_classes = (CustomObjectPermissions,)
    filter_backends = (filters.DjangoObjectPermissionsFilter,)
    
class ContentChannelViewSet(viewsets.ModelViewSet):
    queryset = ContentChannel.objects.all()
    serializer_class = ContentChannelSerializer
    permission_classes = (CustomObjectPermissions,)
    filter_backends = (filters.DjangoObjectPermissionsFilter,)

class ContentTagViewSet(viewsets.ModelViewSet):
    queryset = ContentTag.objects.all()
    serializer_class = ContentTagSerializer
    permission_classes = (CustomObjectPermissions,)
    filter_backends = (filters.DjangoObjectPermissionsFilter,) 

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class ParentKeywordViewSet(viewsets.ModelViewSet):
    queryset = ParentKeyword.objects.select_related('created_by').all()
    serializer_class = ParentKeywordSerializer
    # permission_classes = (CustomObjectPermissions,)
    # filter_backends = (filters.DjangoObjectPermissionsFilter,) 

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class KeywordViewSet(viewsets.ModelViewSet):
    queryset = Keyword.objects.select_related('parent_keyword', 'created_by').prefetch_related('parent_keyword__created_by', 'keyword_metas', 'planning_months').all()
    serializer_class = KeywordSerializer
    # permission_classes = (CustomObjectPermissions,)
    # filter_backends = (filters.DjangoObjectPermissionsFilter,) 

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class KeywordMetaViewSet(viewsets.ModelViewSet):
    queryset = KeywordMeta.objects.select_related(
        'keyword', 
        'organization', 
        'created_by').prefetch_related(
            'tag', 
            'keyword__parent_keyword', 
            ).all().order_by('keyword__name')
    serializer_class = KeywordMetaSerializer
    # permission_classes = (CustomObjectPermissions,)
    # filter_backends = (filters.DjangoObjectPermissionsFilter,)

    def get_queryset(self):
        queryset = super(KeywordMetaViewSet, self).get_queryset()
        organization = self.request.query_params.get('organization', None)

        if organization:
            filtered_queryset = queryset.filter(organization=organization)

            if filtered_queryset and filtered_queryset[0]:
                queryset = filtered_queryset

        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class UrlRankingViewSet(viewsets.ModelViewSet):
    queryset = UrlRanking.objects.select_related('keyword').all()
    serializer_class = UrlRankingSerializer
    permission_classes = (CustomObjectPermissions,)
    filter_backends = (filters.DjangoObjectPermissionsFilter,) 

# To be deprecated
class ContentKeywordsViewSet(viewsets.ModelViewSet):
    queryset = ContentKeywords.objects.prefetch_related('organization').all()
    serializer_class = ContentKeywordsSerializer
    permission_classes = (CustomObjectPermissions,)
    filter_backends = (filters.DjangoObjectPermissionsFilter,)
    
class WriterViewSet(viewsets.ModelViewSet):
    queryset = Writer.objects.select_related('user').prefetch_related(
        'user__org_roles', 
        'user__user_preferences', 
        'user__groups', 
        'user__default_role', 
        'user__user_preferences__default_organization',
        'contentWriter',
        ).filter(user__is_active=True)
    serializer_class = WriterSerializer
    permission_classes = (CustomObjectPermissions,)
    filter_backends = (filters.DjangoObjectPermissionsFilter,)

class ArticleTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = ArticleTemplateSerializer
    permission_classes = (CustomObjectPermissions,)
    filter_backends = (filters.DjangoObjectPermissionsFilter,)

    def get_queryset(self):
        queryset = ArticleTemplate.objects.all().order_by('client__dba_name', 'title')
        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        return queryset
    
class OrganizationRequirementsViewSet(viewsets.ModelViewSet):
    queryset = OrganizationRequirements.objects.all()
    serializer_class = OrganizationRequirementsSerializer
    permission_classes = (CustomObjectPermissions,)
    filter_backends = (filters.DjangoObjectPermissionsFilter,)

class BulkContentArticleViewSet(viewsets.ModelViewSet):
    queryset = ContentArticle.objects.all().order_by('client', 'milestone')
    serializer_class = ContentArticleListSerializer
    permission_classes = (CustomObjectPermissions,)
    filter_backends = (filters.DjangoObjectPermissionsFilter,)

    def get_queryset(self):
        queryset = ContentArticle.objects.all().order_by('client')
        queryset = self.get_serializer_class().setup_eager_loading(queryset)

        return queryset
    
class ContentArticleViewSet(viewsets.ModelViewSet):
    queryset = ContentArticle.objects.all().order_by('client', 'milestone')
    serializer_class = ContentArticleSerializer
    permission_classes = (CustomObjectPermissions,)
    filter_backends = (filters.DjangoObjectPermissionsFilter,)

    def get_serializer(self, *args, **kwargs):
        if "data" in kwargs:
            data = kwargs["data"]

            # check if many is required
            if isinstance(data, list):
                many = True
                data_ids = []
                for obj in data:
                    data_ids.append(obj['id'])
                articles = self.queryset.filter(id__in=data_ids)
                
                serializer = ContentArticleSerializer(instance=articles, data=data, many=many)
                return serializer     
            else:
                return super(ContentArticleViewSet, self).get_serializer(*args, **kwargs)
        else:
            return super(ContentArticleViewSet, self).get_serializer(*args, **kwargs)

    def get_queryset(self):
        queryset = ContentArticle.objects.exclude(archived=True).order_by('client')
        # queryset = self.get_serializer_class().setup_eager_loading(queryset)
        queryset = ContentArticleSerializer.setup_eager_loading(queryset)
        year = self.request.query_params.get('year', None)
        month = self.request.query_params.get('month', None)
        assigned = self.request.query_params.get('assigned', None)
        lead = self.request.query_params.get('lead', None)
        client = self.request.query_params.get('client', None)
        archives = self.request.query_params.get('archives', None)
        user = self.request.query_params.get('user', None) 
        project = self.request.query_params.get('project', None)
        organization = self.request.query_params.get('organization', None)
        content_status = self.request.query_params.get('contentStatus', None)
        title  = self.request.query_params.get('title', None)
        due_date_status = self.request.query_params.get('dueDateStatus', None)

        if year is not None and month is not None and organization is not None:
            try:
                queryset = queryset.filter(planning_year_month__year=year, planning_year_month__month=month, client__id=organization)

                return queryset
            except:
                pass

        if year is not None and month is not None:
            try:
                queryset = queryset.filter(planning_year_month__year=year, planning_year_month__month=month, client__is_active=True)

                return queryset
            except:
                pass
        
        if project is not None:
            queryset = queryset.filter(project__id=project)

            return queryset
        
        if organization is not None:
            last_twelve_months = PlanningYearMonth.objects.all().order_by('-year', '-month')[:24]
            queryset = queryset.filter(Q(planning_year_month__in=last_twelve_months) | Q(project__complete=False), client__id=organization)

            queryset = queryset.filter(Q(planning_year_month__in=last_twelve_months) | Q(project__complete=False), client__id=organization)

            return queryset

        if client:
            # if self.request.user.has_perm('content_management.view_contentarticle') or self.request.user.is_staff:
            self.permission_classes = (IsAuthenticated,)
            self.filter_backends = ()
            user_orgs = Organization.objects.prefetch_related(
                'user_default_organization', 
                'organization_requirements',
                ).filter(user_roles__user=self.request.user)
            #last_six_months = PlanningYearMonth.objects.all().order_by('-year', '-month')[:6]
            last_twelve_months = PlanningYearMonth.objects.all().order_by('-year', '-month')[:24]
            if archives:
                queryset = queryset.filter(client__in=user_orgs, writer__isnull=False).order_by(
                    '-planning_year_month',
                    'content_type',
                    'title',
                    'status'
                )
            else:
                queryset = queryset.filter(Q(planning_year_month__in=last_twelve_months) | Q(project__isnull=False), client__in=user_orgs, writer__isnull=False).order_by(
                    '-planning_year_month',
                    'content_type',
                    'title',
                    'status'
                    )
            
            return queryset

        if assigned and not user:
            requesting_user = self.request.user
            print('called with assigned and not user')
            # applicable_statuses = [2, 3, 4, 5, 6, 7, 8]
            applicable_statuses = ContentStatus.objects.filter(status_type="Active")
            self.permission_classes = (IsAuthenticated,)
            self.filter_backends = ()

            queryset = queryset.filter(
                Q(editor=requesting_user) |
                Q(writer__user=requesting_user) |
                Q(poster=requesting_user) |
                Q(final_approver=requesting_user) |
                Q(lead=requesting_user),
                Q(planning_year_month__isnull=False) |
                Q(project__isnull=False),
                status__in=applicable_statuses,
                writer__isnull=False,
                archived=False
            ).distinct().order_by('status__order', 'planning_year_month__year', 'planning_year_month__month', 'milestone', 'writer_planned_duedate')

            # print('assigned queryset count is: ', queryset.count())
            # final_review = queryset.filter(final_approver=requesting_user, status__order=7)
            # print('assigned final_review count is: ', final_review.count())
            return queryset

        elif assigned and user:
            print('called with assigned and user')
            requested_user = User.objects.get(id=user)
            # applicable_statuses = [2, 3, 4, 5, 6, 7, 8]
            applicable_statuses = ContentStatus.objects.filter(status_type="Active")
            
            if requested_user:
                queryset = queryset.filter(
                    Q(editor=requested_user) |
                    Q(writer__user=requested_user) |
                    Q(poster=requested_user) |
                    Q(final_approver=requested_user) |
                    Q(lead=requested_user),
                    Q(planning_year_month__isnull=False) |
                    Q(project__isnull=False),
                    status__in=applicable_statuses,
                    writer__isnull=False,
                    archived=False
                ).distinct().order_by('status__order', 'planning_year_month__year', 'planning_year_month__month', 'milestone', 'writer_planned_duedate')

                return queryset

        if lead:
            requesting_user = self.request.user
            # applicable_statuses = [2, 3, 4, 5, 6, 7]
            applicable_statuses = ContentStatus.objects.filter(status_type="Active")
            self.permission_classes = (IsAuthenticated,)
            self.filter_backends = ()

            queryset = queryset.filter(
                Q(planning_year_month__isnull=False) |
                Q(project__isnull=False),
                lead=requesting_user,
                status__in=applicable_statuses,
                writer__isnull=False,
                archived=False
            ).distinct().order_by('status__order', 'planning_year_month__year', 'planning_year_month__month', 'milestone', 'writer_planned_duedate')

            return queryset

        if content_status:
            # queryset = queryset.filter(
            #     Q(planning_year_month__isnull=False) | Q(project__isnull=False),
            #     status__order=content_status, archived=False, writer__isnull=False
            # )
            queryset = queryset.filter(
                Q(planning_year_month__isnull=False) | Q(project__isnull=False),
                status__uid=content_status, archived=False, writer__isnull=False
            )

            return queryset

        if title:
            queryset = queryset.filter(title__icontains=title)

            return queryset

        return queryset
    
class ContentCommentsViewSet(viewsets.ModelViewSet):
    queryset = ContentComments.objects.select_related('article', 'author').prefetch_related('article__status', 'author__org_roles', 'author__user_preferences', 'author__writer', 'author__default_role').all()
    serializer_class = ContentCommentsSerializer
    permission_classes = (CustomObjectPermissions,)
    filter_backends = (filters.DjangoObjectPermissionsFilter,)

    def perform_create(self, serializer):
        content_comment = serializer.save(author=self.request.user)
        assign_perm('view_contentcomments', self.request.user, content_comment)
        content_comment.save()

class OrganizationEditorialRequirementViewSet(viewsets.ModelViewSet):
    queryset = OrganizationEditorialRequirement.objects.select_related('organization').all()
    serializer_class = OrganizationEditorialRequirementSerializer
    permission_classes = (CustomObjectPermissions,)
    filter_backends = (filters.DjangoObjectPermissionsFilter,)
    

class InvitationViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    queryset = InvitationModel.objects.select_related(
        'organization', 
        'inviter', 
        'role').prefetch_related(
            'inviter__org_roles', 
            'inviter__user_preferences', 
            'inviter__default_role', 
            'inviter__writer').exclude(sent=None).order_by('-sent')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return InvitationReadSerializer
        elif self.action == 'send_multiple':
            return InvitationBulkWriteSerializer
        return InvitationWriteSerializer

    def _prepare_and_send(self, invitation, request):
        invitation.inviter = request.user
        invitation.save()
        invitation.send_invitation(request)

    @detail_route(
        methods=['post'], permission_classes=[IsAuthenticated],
        url_path=SEND_URL
    )
    def send(self, request, pk=None):
        invitation = self.get_object()
        self._prepare_and_send(invitation, request)
        content = {'detail': 'Invite sent'}
        return Response(content, status=status.HTTP_200_OK)

    @list_route(
        methods=['post'], permission_classes=[IsAuthenticated],
        url_path=CREATE_AND_SEND_URL
    )
    def create_and_send(self, request):
        serializer = self.get_serializer(data=request.data)

        def get_object():
            try:
                try:
                    key = serializer.initial_data['key']
                except:
                    return None
                return InvitationModel.objects.get(key=key.lower())
            except InvitationModel.DoesNotExist:
                return None

        invitation = get_object()

        if invitation:
            invitation.delete()

        serializer.is_valid(raise_exception=True)

        # serializer data
        email = serializer.data['email']
        is_writer = serializer.data['is_writer']
        org = serializer.data['organization']
        group = serializer.data['role']
        price = serializer.data['price']
        first_name = serializer.data['first_name']
        last_name = serializer.data['last_name']
        title = serializer.data['title']
        phone_number = serializer.data['phone_number']
        send_invite = serializer.data['send_invite']
        create_user = serializer.data['create_user']
        try:
            receive_reporting_email = serializer.data['receive_reporting_email']
        except:
            receive_reporting_email = False
        try:
            receive_approval_reminders = serializer.data['receive_approval_reminders']
        except:
            receive_approval_reminders = False


        try:
            organization = Organization.objects.get(id=org)
        except:
            organization = None
        try:
            role = Group.objects.get(id=group)
        except:
            role = None

        invitation = InvitationModel.create(
            email=email, 
            organization=organization, 
            role=role, 
            is_writer=is_writer, 
            price=price, 
            inviter=request.user,
            first_name=first_name,
            last_name=last_name,
            title=title,
            phone_number=phone_number,
            send_invite=send_invite,
            create_user=create_user,
            receive_reporting_email=receive_reporting_email,
            receive_approval_reminders=receive_approval_reminders,
            )

        # create_user logic
        if create_user is True:
            new_user = User.objects.create(
                username="{}.{}".format(first_name.lower(), last_name.lower()),
                email=email,
                first_name=first_name,
                last_name=last_name,
                name="{} {}".format(first_name, last_name),
                title=title,
                phone_number=phone_number,
                default_role=role,
            )
            password = User.objects.make_random_password()
            new_user.set_password(password)
            new_user.save()

            if organization and role:
                role = UserOrgRole.objects.create(user=new_user, organization=organization, role=role, receive_reporting_email=receive_reporting_email, receive_approval_reminders=receive_approval_reminders)
                Preferences.objects.get_or_create(user=new_user, default_organization=organization)
                new_user.save()
            if is_writer == True:
                writer = Writer.objects.create(user=new_user, rate=price)
                new_user.save()
            
            email_context = { 
                'name': new_user.name,
                'email': new_user.email,
                'is_writer': is_writer,
                'organization': organization,
                'role': role.role.name,
                'hostname': request.META['HTTP_HOST'],
            }
            subject = 'New User Registration: {}'.format(new_user.name)
            html = render_to_string('api/new_user_registration.html', email_context)
            from_email = '321 Portal <noreply@{0}>'.format(mailgun_domain)
            recipient_list = []
            staff = User.objects.filter(is_staff=True)
            for user in staff:
                email = user.email
                recipient_list.append(email)

            if not settings.DEBUG == True:
                new_user_email = send_mail(
                    subject=subject, 
                    message=html,
                    html_message=html, 
                    from_email=from_email, 
                    recipient_list=recipient_list
                    )

        # send_invite logic
        if send_invite is True and create_user == False:
            self._prepare_and_send(invitation, request)
            content = {'detail': 'Invite sent, not created'}
            return Response(content, status=status.HTTP_200_OK)
        elif send_invite == False and create_user == True:
            user_serializer = UserDetailsSerializer(new_user)
            return Response(user_serializer.data, status=status.HTTP_200_OK)
        elif send_invite == True and create_user == True:
            self._prepare_and_send(invitation, request)
            user_serializer = UserDetailsSerializer(new_user)
            return Response(user_serializer.data, status=status.HTTP_200_OK)
        elif send_invite == False and create_user == False:
            content = {'detail': 'User Invited, but not created or sent'}
            return Response(content, status=status.HTTP_200_OK)
        else:
            content = {'detail': 'Error with send_invite'}
            return Response(content, status=status.HTTP_400_OK)


    @list_route(
        methods=['post'], permission_classes=[IsAuthenticated],
        url_path=SEND_MULTIPLE_URL
    )
    def send_multiple(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        inviter = request.user
        for email in serializer.data['email']:
            invitation = InvitationModel.create(email=email, inviter=inviter)
            self._prepare_and_send(invitation, request)
        content = {'detail': 'Invite(s) sent'}
        return Response(content, status=status.HTTP_200_OK)



@api_view(('POST', 'GET'))
@permission_classes((AllowAny,))
def accept_invitation(request, key):
    def get_object():
        try:
            return InvitationModel.objects.get(key=key.lower())
        except InvitationModel.DoesNotExist:
            return None

    invitation = get_object()

    login_data = {
        'LOGIN_REDIRECT': invitations_settings.LOGIN_REDIRECT
    }
    signup_data = {
        'SIGNUP_REDIRECT': invitations_settings.SIGNUP_REDIRECT,
    }

    if invitation:
        signup_data.update(
            {
                'account_verified_email': invitation.email
            }
        )

    if invitations_settings.GONE_ON_ACCEPT_ERROR and \
        (not invitation or
         (invitation and (invitation.accepted or
                          invitation.key_expired()))):
        return Response({'Unauthorized': "Invalid Invitation"}, status=status.HTTP_410_GONE)

    if not invitation:
        return Response(login_data, status=status.HTTP_200_OK)

    if invitation.accepted:
        return Response(login_data, status=status.HTTP_200_OK)

    if invitation.key_expired():
        return Response(signup_data, status=status.HTTP_200_OK)

    if not invitations_settings.ACCEPT_INVITE_AFTER_SIGNUP:
        invitation.accepted = True
        invitation.save()
        invite_accepted.send(sender=None, email=invitation.email)
    return Response(
        signup_data,
        status=status.HTTP_200_OK
    )

class UpdateArticleStatus(APIView):
    serializer_class = WriterContentArticleSerializer

    def post(self, request, format=None):
        serializer = WriterContentArticleSerializer(data=request.data)
        if request.user.has_perm('content_management.view_contentarticle'):

            if serializer.is_valid():
                article_id = serializer.data.get('articleId')
                to_status = serializer.data.get('to_status')
                scheduled_date = serializer.data.get('scheduled_date')
                writer_planned_duedate = serializer.data.get('writer_planned_duedate')
                admin_draft_url = serializer.data.get('admin_draft_url')
                live_url = serializer.data.get('live_url')

                print(f'admin_draft_url is: {admin_draft_url}')

                try:
                    article = ContentArticle.objects.get(id=article_id)
                except:
                    article = None
                    return Response({"message": "Article not found"}, status=status.HTTP_400_BAD_REQUEST)
 
                try:
                    # newStatus = ContentStatus.objects.get(order=to_status)
                    newStatus = ContentStatus.objects.get(uid=to_status)
                except:
                    newStatus = None
                    return Response({"message": "Status not found"}, status=status.HTTP_400_BAD_REQUEST)
                    
                # if article.writer.user == request.user or article.editor == request.user or article.poster == request.user or article.final_approver == request.user or request.user.is_staff: 
                if request.user.has_perm('content_management.change_contentarticle'):
                    if scheduled_date:
                        article.scheduled_date = scheduled_date
                    # if to_status == article.status.order:
                    if to_status == article.status.uid and writer_planned_duedate:
                        article.writer_planned_duedate = writer_planned_duedate
                    if to_status == 'scheduled' and live_url:
                        article.live_url = live_url
                    if to_status == 'post_qa' and admin_draft_url:
                        print(f'admin_draft_url is: {admin_draft_url} and hit correct block')
                        article.admin_draft_url = admin_draft_url
                    if newStatus:
                        if to_status == 'editing' and article.writer.user == request.user:
                            try:
                                milestone_articles = ContentArticle.objects.filter(
                                    writer=article.writer, 
                                    milestone=article.milestone, 
                                    planning_year_month=article.planning_year_month
                                    )
                                if milestone_articles.count() <= 1:
                                    writer = article.writer.user.name
                                    planning_month = article.planning_year_month
                                    subject = '{0} has completed all their writing assignments for {1}'.format(writer, planning_month)
                                    email_body = '{0} has completed all their writing assignments for {1}'.format(writer, planning_month)
                                    hostname = request.META['HTTP_HOST']

                                    from_email = '321 Portal <noreply@{0}>'.format(mailgun_domain)
                                    template = 'api/completed_assignments.html'
                                    recipient_list = []
                                    staff = User.objects.filter(is_staff=True)
                                    for user in staff:
                                        email = user.email
                                        recipient_list.append(email)

                                    email_context = { 
                                        'email_body': email_body,
                                    }

                                    writer_completed_email = send_mail(subject, email_body, from_email, recipient_list)
                                    writer_completed_email = send_email(
                                        template=template,
                                        recipients=recipient_list,
                                        subject=subject,
                                        context=email_context,
                                    )
 
                            except:
                                pass
                    article.status = newStatus
                    article.save()
                else:
                    return Response({'Unauthorized': "You do not have permissions to do that."},
                    status=status.HTTP_401_UNAUTHORIZED)
                
                return Response({"message": "Article Status Updated!"}, status=status.HTTP_200_OK)
            return Response({"message": "Serializer not valid"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'Unauthorized': "You do not have permissions to do that."},
                    status=status.HTTP_401_UNAUTHORIZED)


class CreateGoogleDocView(APIView):
    serializer_class = CreateGoogleDocSerializer

    def get(self, request, format=None):
        return Response({"message": "Not Applicable"})

    def post(self, request, format=None):
        serializer = CreateGoogleDocSerializer(data=request.data)
        if request.user.has_perm('content_management.create_google_doc'):

            if serializer.is_valid():
                organization = serializer.data.get('organization')
                year = serializer.data.get('year')
                month = serializer.data.get('month')
                projectId = serializer.data.get('projectId')
                title = serializer.data.get('title')
                article_id = serializer.data.get('articleId')

                try:
                    article = ContentArticle.objects.get(id=article_id)
                except:
                    article = None

                try:
                    project = ContentProject.objects.get(id=projectId)
                except:
                    project = None

                if project:
                    valid_project_folder = search_drive_files(name=project.name)
                    if not valid_project_folder:
                        valid_project_folder = create_drive_file(name=project.name, isFolder=True)
                    
                    new_file = create_drive_file(name=title, isFolder=False, parent=valid_project_folder)

                else:
                    valid_org_folder = search_drive_files(name=organization)
                    if not valid_org_folder:
                        valid_org_folder = create_drive_file(name=organization, isFolder=True)

                    valid_year_folder = search_drive_files(name=year, folder=valid_org_folder)
                    if not valid_year_folder:
                        valid_year_folder = create_drive_file(name=year, isFolder=True, parent=valid_org_folder)
                    
                    valid_month_folder = search_drive_files(name=month, folder=valid_year_folder)
                    if not valid_month_folder:
                        valid_month_folder = create_drive_file(name=month, isFolder=True, parent=valid_year_folder)
                    
                    new_file = create_drive_file(name=title, isFolder=False, parent=valid_month_folder)


                google_doc_url = 'https://docs.google.com/document/d/{0}/edit'.format(new_file)

                if article:
                    article.google_doc = google_doc_url
                    article.save()
                    
                return Response({"fileId": new_file, "url": google_doc_url}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'Unauthorized': "You do not have permissions to do that."},
                        status=status.HTTP_401_UNAUTHORIZED)

