from rest_framework import serializers
from organizations.serializers import OrganizationSerializer
from docker_drf_backend.users.models import User, Preferences, UserOrgRole
from content_management.models import Writer
from rest_framework import mixins, status, permissions
from django.contrib.auth.tokens import default_token_generator
from rest_auth.models import TokenModel
from rest_auth.serializers import UserDetailsSerializer
from django.db import models
from django.db.models import Prefetch
from django.conf import settings
from django.contrib.auth import get_user_model
import json
from guardian.shortcuts import assign_perm, remove_perm, get_group_perms
from django.db import transaction
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.forms import PasswordResetForm
from django.db.models import Count
from rest_framework.response import Response
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied
import datetime
try:
    from allauth.account import app_settings as allauth_settings
    from allauth.utils import (email_address_exists,
                               get_username_max_length)
    from allauth.account.adapter import get_adapter
    from allauth.account.utils import setup_user_email
    from allauth.socialaccount.helpers import complete_social_login
    from allauth.socialaccount.models import SocialAccount
    from allauth.socialaccount.providers.base import AuthProcess
except ImportError:
    raise ImportError("allauth needs to be added to INSTALLED_APPS.")

UserModel = get_user_model()

class GroupSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Group
        fields = ('id', 'name')

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ('id', 'name', 'codename')

class UserOrgRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserOrgRole
        fields = ('__all__')

class DetailedUserOrgRoleSerializer(serializers.ModelSerializer):
    user = UserDetailsSerializer(many=False, read_only=True)
    class Meta:
        model = UserOrgRole
        fields = ('__all__')

class PreferencesSerializer(serializers.ModelSerializer):
    default_organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = Preferences
        fields = (
           "__all__"
        )

class WriterDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Writer
        fields = ('__all__')

class BriefUserDetailsSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    user_preferences = PreferencesSerializer(read_only=True)
    org_roles = UserOrgRoleSerializer(read_only=True, many=True)
    writer = WriterDetailsSerializer(read_only=True)
    default_role = GroupSerializer(read_only=True)

    def get_avatar_url(self, obj):
        if obj.avatar and self.context:
            return self.context['request'].build_absolute_uri(obj.avatar.url)
    
    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related(
            'default_role', 
        )

        queryset = queryset.prefetch_related(
            'user_preferences', 
            'org_roles',
            'contentWriter',
            'contentEditor',
            'contentPoster',
            'contentApprover',
            'contentLead', 
            'groups', 
            'writer', 
            'user_preferences__default_organization', 
            )

        return queryset

    class Meta:
        model = UserModel
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'avatar_url',
            'user_preferences',
            'name',
            'title',
            'phone_number',
            'is_active',
            'default_role',
            'org_roles',
            'is_staff',
            'writer',
        )

class QuickUserDetailsSerializer(serializers.ModelSerializer):

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related(
            'default_role', 
        )

        queryset = queryset.prefetch_related(
            'user_preferences', 
            'org_roles',
            'contentWriter',
            'contentEditor',
            'contentPoster',
            'contentApprover',
            'contentLead',
            'user_permissions', 
            'groups', 
            'writer', 
            'user_preferences__default_organization', 
            'checklist_template_item_assignments'
            )

        return queryset

    class Meta:
        model = UserModel
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'name',
            'title',
            'phone_number',
            'is_active',
            'is_staff',
            'is_superuser',
        )

class PermissionListingField(serializers.RelatedField):
    def to_representation(self, value):
        serializer = PermissionSerializer()
        return serializer.data

class UserDetailsSerializer(serializers.ModelSerializer):

    org_roles = UserOrgRoleSerializer(read_only=True, many=True)
    user_preferences = PreferencesSerializer(allow_null=True, read_only=True)
    writer = WriterDetailsSerializer(read_only=True)

    def to_representation(self, instance):
        response = super(UserDetailsSerializer, self).to_representation(instance)
        response['default_role'] = GroupSerializer(instance.default_role).data
 
        if not instance.is_superuser:
            permission_query = Permission.objects.select_related('content_type').filter(group__user=instance).distinct()
            response['permissions'] = PermissionSerializer(permission_query, many=True, read_only=True).data
        return response
    
    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related(
            'default_role', 
        )

        queryset = queryset.prefetch_related(
            'user_preferences', 
            'org_roles',
            'org_roles__organization',
            'contentWriter',
            'contentEditor',
            'contentPoster',
            'contentApprover',
            'contentLead',
            'user_permissions', 
            'groups', 
            'writer', 
            'user_preferences__default_organization', 
            )

        return queryset

    class Meta:
        model = UserModel
        fields = (
            'id', 
            'username',
            'default_role',
            'email', 
            'is_superuser', 
            'is_staff', 
            'first_name', 
            'last_name',
            'name',
            'title',
            'phone_number',
            'avatar',
            'org_roles',
            'user_preferences',
            'writer',
            'date_joined',
            'last_login',
            'is_active',
            'user_permissions',
            )
        read_only_fields = (
            'id',
            'username',
            'email',
            'is_superuser',
            'is_staff',
            'date_joined',
            'last_login',
            'user_permissions',
        )


class TokenSerializer(serializers.ModelSerializer):
    token = serializers.CharField(source='key')
    user = UserDetailsSerializer(many=False, read_only=True, default=serializers.CurrentUserDefault())

    def to_representation(self, instance):
        response = super(TokenSerializer, self).to_representation(instance)
        request = self.context.get("request")

        as_user = request.query_params.get('as', None)

        if as_user is not None:
            if request.user.is_superuser:
                try:
                    if isinstance(as_user, int):
                        ghost_user = User.objects.get(id=as_user)
                    else:
                        ghost_user = User.objects.get(Q(username=as_user) | Q(email=as_user))
                except:
                    ghost_user = None

                if ghost_user:
                    if ghost_user.is_superuser:
                        raise PermissionDenied("You are not authorized to login as another super user.")
                    else:
                        ghost_user_token, created = TokenModel.objects.get_or_create(user=ghost_user)

                        if ghost_user and ghost_user_token:
                            ghost_user_response = UserDetailsSerializer(ghost_user,  context={'request': request}).data

                            response["ghost_user"] = ghost_user_response
                            response["ghost_user_token"] = json.dumps(ghost_user_token.key).strip('"')
            else:
                raise PermissionDenied("You are not authorized to perform this action")


        return response

    class Meta:
        model = TokenModel
        fields = ('token', 'user')

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=get_username_max_length(),
        min_length=allauth_settings.USERNAME_MIN_LENGTH,
        required=allauth_settings.USERNAME_REQUIRED
    )
    email = serializers.EmailField(required=allauth_settings.EMAIL_REQUIRED)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    title = serializers.CharField()
    phone_number = serializers.CharField(required=True, max_length=17)
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    key = serializers.CharField(required=True)

    def validate_username(self, username):
        username = get_adapter().clean_username(username)
        return username

    def validate_email(self, email):
        email = get_adapter().clean_email(email)
        if allauth_settings.UNIQUE_EMAIL:
            if email and email_address_exists(email):
                raise serializers.ValidationError(
                    _("A user is already registered with this e-mail address."))
        return email

    def validate_password1(self, password):
        return get_adapter().clean_password(password)

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError(_("The two password fields didn't match."))
        return data
    

    def custom_signup(self, request, user):
        pass

    def get_cleaned_data(self):
        return {
            'username': self.validated_data.get('username', ''),
            'first_name': self.validated_data.get('first_name', ''),
            'last_name': self.validated_data.get('last_name', ''),
            'title': self.validated_data.get('title', ''),
            'phone_number': self.validated_data.get('phone_number', ''),
            'name':  "{} {}".format(self.validated_data.get('first_name', ''), self.validated_data.get('last_name', '')),
            'password1': self.validated_data.get('password1', ''),
            'email': self.validated_data.get('email', '')
        }

    def save(self, request):
        adapter = get_adapter()
        user = adapter.new_user(request)
        self.cleaned_data = self.get_cleaned_data()
        adapter.save_user(request, user, self)
        self.custom_signup(request, user)
        setup_user_email(request, user, [])
        return user

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password_reset_form_class = PasswordResetForm

    def validate_email(self, value):
        self.reset_form = self.password_reset_form_class(data=self.initial_data)
        if not self.reset_form.is_valid():
            raise serializers.ValidationError(_('Error'))

        if not User.objects.filter(email=value).exists():

            raise serializers.ValidationError(_('Invalid e-mail address'))
        return value

    def save(self):
        request = self.context.get('request')
        opts = {
            'use_https': request.is_secure(),
            'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL'),

            'email_template_name': 'password_reset_email.txt',

            'request': request,
        }
        self.reset_form.save(**opts)


class ChangePasswordSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True, allow_null=False)
    password1 = serializers.CharField(required=True, allow_null=False)
    password2 = serializers.CharField(required=True, allow_null=False)

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError(_("The two password fields didn't match."))
        return data

    def get_cleaned_data(self):
        return {
            'password1': self.validated_data.get('password1', ''),
            'password2': self.validated_data.get('password2', ''),
        }
