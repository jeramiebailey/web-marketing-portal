from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from rest_framework.response import Response
from django.views.generic import DetailView, ListView, RedirectView, UpdateView
from rest_framework import viewsets, permissions, mixins, status
from django.conf import settings
from docker_drf_backend.users.models import User, UserOrgRole, Preferences
from django.contrib.auth.models import Group, Permission
from rest_auth.registration.app_settings import RegisterSerializer, register_permission_classes
from allauth.account import app_settings as allauth_settings
from rest_auth.app_settings import (TokenSerializer,
                                    JWTSerializer,
                                    create_token)
from rest_auth.registration.views import RegisterView
from rest_framework.views import APIView
from rest_framework.decorators import (api_view, detail_route, list_route,
                                       permission_classes)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_guardian import filters
from api.permissions import CustomObjectPermissions
from guardian.shortcuts import get_objects_for_user, get_perms
from rest_auth.utils import jwt_encode
from django.db.models import Prefetch
from django.template.loader import render_to_string
from guardian.shortcuts import assign_perm, remove_perm
import environ
from django.db.models import Q
from user_onboarding.models import CustomInvitation
from rest_framework.decorators import action
from django.core.mail import send_mail
from django.db import transaction
from docker_drf_backend.users.serializers import PreferencesSerializer, UserDetailsSerializer, BriefUserDetailsSerializer, QuickUserDetailsSerializer, UserOrgRoleSerializer, DetailedUserOrgRoleSerializer, ChangePasswordSerializer, PermissionSerializer, GroupSerializer
from organizations.models import Organization
from content_management.models import Writer
from allauth.account.utils import complete_signup
from content_management.serializers import BriefContentArticleSerializer

User = get_user_model()
env = environ.Env()

google_api_key = env('GOOGLE_API_KEY')
mailgun_api_key = env('MAILGUN_API_KEY')
mailgun_domain = 'mg.321webmarketing.com'

class UserDetailView(LoginRequiredMixin, DetailView):

    model = User
    slug_field = "username"
    slug_url_kwarg = "username"


user_detail_view = UserDetailView.as_view()


class UserListView(LoginRequiredMixin, ListView):

    model = User
    slug_field = "username"
    slug_url_kwarg = "username"


user_list_view = UserListView.as_view()


class UserUpdateView(LoginRequiredMixin, UpdateView):

    model = User
    fields = ["name"]

    def get_success_url(self):
        return reverse("users:detail", kwargs={"username": self.request.user.username})

    def get_object(self):
        return User.objects.get(username=self.request.user.username)


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):

    permanent = False

    def get_redirect_url(self):
        return reverse("users:detail", kwargs={"username": self.request.user.username})


user_redirect_view = UserRedirectView.as_view()

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.prefetch_related('permissions').all()
    serializer_class = GroupSerializer


class PermissionViewSet(viewsets.ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer

class PreferencesViewSet(viewsets.ModelViewSet):
    queryset = Preferences.objects.select_related('user', 'default_organization').all()
    permission_classes = (CustomObjectPermissions,)
    serializer_class = PreferencesSerializer
    filter_backends = (filters.DjangoObjectPermissionsFilter,)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.select_related('default_role').prefetch_related(
            'user_preferences', 
            'org_roles',
            'org_roles__organization',
            'user_permissions',
            'checklist_template_item_assignments',
            'groups', 
            'writer', 
            'user_preferences__default_organization',
            ).exclude(Q(username="AnonymousUser") | Q(is_active=False)).order_by('user_preferences__default_organization', 'name')
    permission_classes = (CustomObjectPermissions,)
    serializer_class = UserDetailsSerializer
    filter_backends = (filters.DjangoObjectPermissionsFilter,)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserDetailsSerializer
        else:
            return BriefUserDetailsSerializer
        return UserDetailsSerializer


    def get_queryset(self):
        queryset = User.objects.select_related('default_role').prefetch_related(
            'user_preferences', 
            'org_roles',
            'user_permissions', 
            'groups', 
            'writer', 
            'user_preferences__default_organization', 
            'checklist_template_item_assignments',).exclude(Q(username="AnonymousUser") | Q(is_active=False)).order_by('user_preferences__default_organization', 'name')

        internal = self.request.query_params.get('internal', None)
        org = self.request.query_params.get('org', None)
        
        if internal:
            try:
                organization = Organization.objects.get(dba_name='321 Web Marketing')
            except:
                organization = None
            
            queryset = queryset.filter(org_roles__organization=organization)

        
        if org is not None:
            try:
                found_organization = Organization.objects.get(Q(id=org) | Q(slug=org))
            except:
                found_organization = None

            if found_organization:
                queryset = queryset.filter(org_roles__organization=found_organization)

        return queryset


    @action(detail=True, methods=['get'])
    def get_current_assignments(self, request, pk=None):
        instance = self.get_object()
        countOnly = self.request.query_params.get('countOnly', None)
        if request.user.has_perm('content_management.view_contentarticles') or self.request.user.is_staff:
            current_assignments = instance.get_all_content_assignments()

            if countOnly:
                response = {
                    'count': current_assignments.count()
                }
                return Response(response, status=status.HTTP_200_OK)
            else:
                response = BriefContentArticleSerializer(current_assignments, many=True)
        
                return Response(response.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def get_late_assignments(self, request, pk=None):
        instance = self.get_object()
        countOnly = self.request.query_params.get('countOnly', None)
        if request.user.has_perm('content_management.view_contentarticles') or self.request.user.is_staff:
            late_assignments = instance.get_all_late_assignments()

            if countOnly:
                response = {
                    'count': late_assignments.count()
                }
                return Response(response, status=status.HTTP_200_OK)
            else:
                response = BriefContentArticleSerializer(late_assignments, many=True)

                return Response(response.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def get_due_soon_assignments(self, request, pk=None):
        instance = self.get_object()
        countOnly = self.request.query_params.get('countOnly', None)
        if request.user.has_perm('content_management.view_contentarticles') or self.request.user.is_staff:
            due_soon_assignments = instance.get_due_soon_assignments()

            if countOnly:
                response = {
                    'count': due_soon_assignments.count()
                }
                return Response(response, status=status.HTTP_200_OK)
            else:
                response = BriefContentArticleSerializer(due_soon_assignments, many=True)

                return Response(response.data, status=status.HTTP_200_OK)

class UserOrgRoleViewSet(viewsets.ModelViewSet):
    queryset = UserOrgRole.objects.all()
    serializer_class = UserOrgRoleSerializer
    permission_classes = [permissions.IsAuthenticated,]

    def get_serializer_class(self):
        detailed = self.request.query_params.get('detailed', None)

        if detailed:
            return DetailedUserOrgRoleSerializer
        else:
            return UserOrgRoleSerializer
    
    def get_queryset(self):
        queryset = super(UserOrgRoleViewSet, self).get_queryset()
        user = self.request.user

        if user.is_staff:
            organization = self.request.query_params.get('organization', None)
            if organization is not None:
                try:
                    found_organization = Organization.objects.get(Q(id=organization) | Q(slug=organization))
                except:
                    found_organization = None
                if found_organization:
                    queryset = queryset.select_related('organization', 'user', 'role').filter(organization=found_organization)
            return queryset
        else:
            return queryset.filter(user=user)

class MyRegisterView(RegisterView):
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = str(serializer.data['email'])
        first_name = str(serializer.data['first_name'])
        last_name = str(serializer.data['last_name'])
        title = str(serializer.data['title'])
        phone_number = str(serializer.data['phone_number'])
        key = str(serializer.data['key'])
        try:
            valid_invitation = CustomInvitation.objects.get(email=email, key=key, accepted=False)
        except:
            valid_invitation = False

        if valid_invitation:
            user = self.perform_create(serializer)
            user.default_role = valid_invitation.role
            user.first_name = first_name
            user.last_name = last_name
            user.title = title
            user.phone_number = phone_number
            user.name = "{} {}".format(first_name, last_name)
            user.save()
            valid_invitation.accepted = True
            valid_invitation.save()
            if valid_invitation.organization and valid_invitation.role:
                UserOrgRole.objects.create(user=user, organization=valid_invitation.organization, role=valid_invitation.role)
                Preferences.objects.get_or_create(user=user, default_organization=valid_invitation.organization)
            if valid_invitation.is_writer == True:
                writer = Writer.objects.create(user=user, rate=valid_invitation.price)
                is_writer = True
            else:
                is_writer = False

            response_data = self.get_response_data(user)
            headers = self.get_success_headers(serializer.data)

            email_context = { 
                'name': user.name,
                'email': user.email,
                'is_writer': is_writer,
                'organization': valid_invitation.organization,
                'role': valid_invitation.role,
                'hostname': request.META['HTTP_HOST'],
            }
            subject = 'New User Registration: {}'.format(user.name)
            html = render_to_string('api/new_user_registration.html', email_context)
            from_email = '321 Portal <noreply@{0}>'.format(mailgun_domain)
            recipient_list = []
            staff = User.objects.filter(is_staff=True)
            for user in staff:
                email = user.email
                recipient_list.append(email)

            new_user_email = send_mail(
                subject=subject, 
                message=html,
                html_message=html, 
                from_email=from_email, 
                recipient_list=recipient_list
                )

            return Response(response_data,
                        status=status.HTTP_201_CREATED,
                        headers=headers)
        else:
            return Response({'Unauthorized': "Invalid Invitation"},
                        status=status.HTTP_401_UNAUTHORIZED)
    
    def perform_create(self, serializer):
        user = serializer.save(self.request)

        if getattr(settings, 'REST_USE_JWT', False):
            self.token = jwt_encode(user)
        else:
            create_token(self.token_model, user, serializer)

        complete_signup(self.request._request, user,
                        allauth_settings.EMAIL_VERIFICATION,
                        None)
        return user

# NOTE: this is bad and we should not implement this down the line
class UserPasswordChangeView(APIView):
    serializer_class = ChangePasswordSerializer

    def get(self, request, format=None):
        requesting_user = request.user
        if requesting_user and requesting_user.is_superuser:
            return Response({"message": "Please provide new password"})
        else:
            return Response(
                            {
                                "response": "Unauthorized",
                            }, status=status.HTTP_401_UNAUTHORIZED)

    def post(self, request, format=None):
        requesting_user = request.user
        if requesting_user and requesting_user.is_superuser:
            serializer = ChangePasswordSerializer(data=request.data)

            if serializer.is_valid():
                user_id = serializer.data.get('user_id')
                password1 = serializer.data.get('password1')
                password2 = serializer.data.get('password2')

                try:
                    user = User.objects.get(pk=user_id)
                except:
                    user = None

                if user:
                    if not user.is_superuser or not user.is_staff:
                        if password1 == password2:

                            user.set_password(password1)
                            user.save()

                            return Response(
                                        {
                                            "response": "Password Successfully Changed.",
                                        }, status=status.HTTP_200_OK)
                        
                        return Response(
                                            {
                                                "response": "Passwords do not match",
                    
                                            }, status=status.HTTP_400_BAD_REQUEST)

                    else:
                        return Response(
                            {
                                "response": "Unauthorized",
                            }, status=status.HTTP_401_UNAUTHORIZED)

                return Response(
                                    {
                                        "response": "User not found",
                                        "errors": serializer.errors,
                                    }, status=status.HTTP_404_NOT_FOUND)
            
            return Response(
                                    {
                                        "response": "Invalid Request",
                                        "errors": serializer.errors,
                                    }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                            {
                                "response": "Unauthorized",
                            }, status=status.HTTP_401_UNAUTHORIZED)