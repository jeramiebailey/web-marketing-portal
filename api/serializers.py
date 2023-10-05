from rest_framework import serializers
from docker_drf_backend.users.models import User, Preferences, UserOrgRole
from notifications.models import Notification

from django.http import HttpRequest
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.db.models import Prefetch
from django.conf import settings
from django.contrib.auth import get_user_model
from invitations.utils import get_invitation_model
from invitations.adapters import get_invitations_adapter
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
from guardian.shortcuts import assign_perm, remove_perm, get_group_perms
from requests.exceptions import HTTPError
from user_onboarding.models import CustomInvitation
from django.db import transaction
from django.contrib.auth.models import Group, Permission
from organizations.models import Organization, Address
from invitations.exceptions import (AlreadyAccepted, AlreadyInvited,
                                    UserRegisteredEmail)
from content_management.models import PlanningYearMonth, ContentStatus, ContentType, ContentChannel, ContentKeywords, Writer, ContentArticle, ContentComments, ArticleTemplate, OrganizationRequirements, ParentKeyword, Keyword, KeywordMeta, ContentTag, UrlRanking, OrganizationEditorialRequirement, ContentProject
from django.db.models import Count
from django.db.models import Q
import datetime
from django.contrib.contenttypes.models import ContentType as ContentObjectType
from organizations.serializers import WhatConvertsAccountSerializer
import json
from content_management.tasks import assign_article_permissions, cascade_article_templates
from organizations.serializers import OrganizationSerializer, DetailedOrganizationSerializer
from docker_drf_backend.users.serializers import QuickUserDetailsSerializer, UserDetailsSerializer, GroupSerializer
from dateutil.relativedelta import *

InvitationModel = get_invitation_model()

UserModel = get_user_model()

errors = {
    "already_invited": _("This e-mail address has already been"
                         " invited."),
    "already_accepted": _("This e-mail address has already"
                          " accepted an invite."),
    "email_in_use": _("An active user is using this e-mail address"),
}

class DynamicHyperlinkedRelatedField(serializers.HyperlinkedRelatedField):

    def get_url(self, obj, view_name, request, format):
        if hasattr(obj, 'pk') and obj.pk in (None, ''):
            return None

        model_name_lower = obj._meta.object_name.lower()

        try:
            api_view_name = obj.get_api_view_name()
            view_name = f'api:{api_view_name}-detail'
        except:
            view_name=f'api:{model_name_lower}s-detail'

        self.view_name = view_name

        data = super(DynamicHyperlinkedRelatedField, self).get_url(obj, view_name, request, format)
        return data

class ContentObjectTypeSerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        response = super().to_representation(instance)
        model_name = instance.model_class()._meta.verbose_name.title()
        # field_names = [field.name for field in instance.model_class()._meta.get_fields()]
        field_names = [field.name for field in instance.model_class()._meta.concrete_fields
                             if field.name != 'id' and field.name != 'password' and
                                not isinstance(field, models.ForeignKey) and not isinstance(field, models.ManyToManyField)]
        response['model_name'] = model_name
        response['fields'] = field_names
        return response
    class Meta:
        model = ContentObjectType
        fields = ('__all__')



class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'text')

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ('__all__')

class OrganizationEditorialRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationEditorialRequirement
        fields = ('__all__')

class OrganizationRequirementsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationRequirements
        fields = ('__all__')


class BriefPlanningYearMonthSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanningYearMonth
        fields = ('__all__')

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related(
            Prefetch('contentArticle', queryset=ContentArticle.objects.select_related('status', 'planning_year_month').all()),
        )
        queryset = queryset.prefetch_related('contentArticle', 'contentArticle__status', 'contentArticle__status__contentStatus')
        return queryset

class BriefContentProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentProject
        fields = ('__all__')

class PlanningYearMonthSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = PlanningYearMonth
        fields = ('__all__')

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.prefetch_related(
            Prefetch('contentArticle', queryset=ContentArticleSerializer.setup_eager_loading(ContentArticle.objects.all())),
        )
        queryset = queryset.prefetch_related(
            'contentArticle', 
            'contentArticle__status', 
            'contentArticle__status__contentStatus', 
            'contentArticle__planning_year_month')
        return queryset

    def to_representation(self, instance):
        response = super(PlanningYearMonthSerializer, self).to_representation(instance)
        response = dict(response, **instance.get_article_statuses())

        return response
        

    def create(self, validated_data):
        instance = PlanningYearMonth.objects.create(**validated_data)
        instance.save()
        article_templates = ArticleTemplate.objects.filter(archived=False)
        try:
            # backlog = ContentStatus.objects.get(order=1)
            backlog = ContentStatus.objects.get(uid='backlog')
        except:
            backlog = None

        created_articles = cascade_article_templates(instance.id)

        return instance

class ContentProjectSerializer(serializers.ModelSerializer):

    @staticmethod
    def setup_eager_loading(queryset):
        # queryset = queryset.prefetch_related(
        #     Prefetch('project_articles', queryset=ContentArticle.objects.select_related('status', 'project').all()),
        # )
        content_articles = Prefetch('project_articles', queryset=ContentArticleSerializer.setup_eager_loading(ContentArticle.objects.all()))
        statuses = Prefetch('project_articles__status', queryset=ContentStatus.objects.select_related('contentStatus', 'contentStatus__project', 'contentStatus__planning_year_month'))

        queryset = queryset.prefetch_related(content_articles, statuses)
        # queryset = queryset.prefetch_related(
        #     'project_articles',
        #     'project_articles__status', 
        #     'project_articles__status__contentStatus', 
        #     'project_articles__project')
        return queryset

    def to_representation(self, instance):
        response = super(ContentProjectSerializer, self).to_representation(instance)
        response = dict(response, **instance.get_article_statuses())

        return response
    
    class Meta:
        model = ContentProject
        fields = ('__all__')

class ContentStatusSerializer(serializers.ModelSerializer):

    @staticmethod
    def setup_eager_loading(queryset):

        queryset = queryset.prefetch_related(
            'related_default_months', 
            'contentStatus',
            )

        return queryset
    class Meta:
        model = ContentStatus
        fields = ('__all__')

class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = ('__all__')

class ContentChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentChannel
        fields = ('__all__')

class ContentTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentTag
        fields = ('__all__')

class ParentKeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentKeyword
        fields = [
            'id',
            'name',
            'active',
        ]

class KeywordSerializer(serializers.ModelSerializer):
    parent_keyword = ParentKeywordSerializer()

    def create(self, validated_data):
        user = self.context['request'].user
        parent_keyword_data = validated_data.pop('parent_keyword')
        parent_keyword_data.pop('created_by')
        parent_keyword, created = ParentKeyword.objects.get_or_create(created_by=user, **parent_keyword_data)
        keyword = Keyword.objects.create(parent_keyword=parent_keyword, **validated_data)
        keyword.save()

        return keyword
    
    def update(self, instance, validated_data):
        user = self.context['request'].user
        parent_keyword_data = validated_data.pop('parent_keyword')
        parent_keyword_data.pop('created_by')
        parent_keyword, created = ParentKeyword.objects.get_or_create(created_by=user, **parent_keyword_data)
        keyword = Keyword.objects.get(id=instance.id)
        instance = Keyword(id=instance.id, date_created=instance.date_created, **validated_data)
        instance.parent_keyword = parent_keyword
        instance.save()

        return instance

    class Meta:
        model = Keyword
        fields = [
            'id',
            'name',
            'parent_keyword',
            'difficulty',
            'volume',
            'cost_per_click',
            'active',
        ]

class KeywordMetaSerializer(serializers.ModelSerializer):
    keyword = KeywordSerializer()

    def create(self, validated_data):
        user = self.context['request'].user
        keyword_data = validated_data.pop('keyword')
        try:
            keyword_created_by = keyword_data.pop('created_by')
        except:
            keyword_created_by = user
        parent_keyword_data = keyword_data.pop('parent_keyword')
        try:
            parent_keyword_created_by = parent_keyword_data.pop('created_by')
        except:
            parent_keyword_created_by = user
        parent_keyword, parent_keyword_created = ParentKeyword.objects.get_or_create(created_by=keyword_created_by, **parent_keyword_data)
        keyword, keyword_created = Keyword.objects.get_or_create(created_by=parent_keyword_created_by, parent_keyword=parent_keyword, **keyword_data)
        tags = validated_data.pop('tag')
        planning_months = validated_data.pop('planning_months')
        keyword_meta = KeywordMeta.objects.create(keyword=keyword, **validated_data)
        keyword_meta.tag.set(tags)
        keyword_meta.planning_months.set(planning_months)
        keyword_meta.save()

        return keyword_meta

    def update(self, instance, validated_data):
        user = self.context['request'].user
        keyword_data = validated_data.pop('keyword')
        try:
            keyword_created_by = keyword_data.pop('created_by')
        except:
            keyword_created_by = user
        parent_keyword_data = keyword_data.pop('parent_keyword')
        try:
            parent_keyword_created_by = parent_keyword_data.pop('created_by')
        except:
            parent_keyword_created_by = user

        parent_keyword, parent_keyword_created = ParentKeyword.objects.get_or_create(created_by=keyword_created_by, **parent_keyword_data)
        # if not parent_keyword_created:
        #     parent_keyword = ParentKeyword(id=parent_keyword.id, date_created=instance.date_created, **parent_keyword_data)
        #     parent_keyword.save()

        keyword, keyword_created = Keyword.objects.get_or_create(created_by=parent_keyword_created_by, parent_keyword=parent_keyword, **keyword_data)

        keyword_meta = KeywordMeta.objects.get(id=instance.id)
        tags = validated_data.pop('tag')
        planning_months = validated_data.pop('planning_months')
        instance = KeywordMeta(id=instance.id, date_created=instance.date_created, **validated_data)
        instance.keyword = keyword
        instance.save()
        instance.tag.set(tags)
        instance.planning_months.set(planning_months)
        instance.save()

        return instance

    # def to_representation(self, instance):
    #     response = super(KeywordMetaSerializer, self).to_representation(instance)
    #     response['organization'] = OrganizationSerializer(instance.organization).data
    #     return response

    class Meta:
        model = KeywordMeta
        fields = [
            'id',
            'keyword',
            'organization',
            'planning_months',
            'tag',
            'seo_value',
            'business_value',
            'active',
        ]

class UrlRankingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UrlRanking
        fields = ('__all__')

# To be deprecated
class ContentKeywordsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentKeywords
        fields = ('__all__')

class WriterSerializer(serializers.ModelSerializer):
    user = QuickUserDetailsSerializer(read_only=True)

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related(
            'user',
        )

        queryset = queryset.prefetch_related(
            'user__org_roles', 
            'user__user_preferences', 
            'user__groups', 
            'user__default_role', 
            'user__user_preferences__default_organization',
            'contentWriter',
            )

        return queryset
    class Meta:
        model = Writer
        fields = ('__all__')


class ContentCommentsSerializer(serializers.ModelSerializer):
    author = QuickUserDetailsSerializer(read_only=True)

    class Meta:
        model = ContentComments
        fields = ('__all__')


class ContentArticleListSerializer(serializers.ListSerializer):
    
    class Meta:
        fields = (
            'id', 
            'lead', 
            'writer', 
            'poster', 
            'final_approver', 
            'status', 
            'duedate_write',
            'duedate_rewrite',
            'duedate_edit',
            'duedate_reedit',
            'duedate_finalreview',
            'duedate_schedulepost',
            'duedate_qapost',
            'duedate_golive',
        )

    def update(self, instance, validated_data):
        article_mapping = {article.id: article for article in instance}

        data_mapping = {item['id']: item for item in validated_data}

        articles = []
        for article_id, data in data_mapping.items():
  
            article = article_mapping.get(article_id, None)
            if article is None:
                articles.append(self.child.create(data))
            else:
                articles.append(self.child.update(article, data))

        for article_id, article in article_mapping.items():
            if article_id not in data_mapping:
                article.delete()

        return articles

class ContentArticleSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    contentComments = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    
    class Meta:
        model = ContentArticle
        list_serializer_class = ContentArticleListSerializer
        fields = ('__all__')
    
    @classmethod
    def many_init(cls, *args, **kwargs):
        # Instantiate the child serializer.
        kwargs['child'] = cls()
        # Instantiate the parent list serializer.
        return ContentArticleListSerializer(*args, **kwargs)
        

    def to_representation(self, instance):
        # response = super().to_representation(instance)
        response = super(ContentArticleSerializer, self).to_representation(instance)
        response['client'] = OrganizationSerializer(instance.client).data
        response['writer'] = WriterSerializer(instance.writer).data
        response['editor'] = QuickUserDetailsSerializer(instance.editor).data
        response['poster'] = QuickUserDetailsSerializer(instance.poster).data
        response['lead'] = QuickUserDetailsSerializer(instance.lead).data
        response['final_approver'] = QuickUserDetailsSerializer(instance.final_approver).data
        response['content_type'] = ContentTypeSerializer(instance.content_type).data
        response['planning_year_month'] = BriefPlanningYearMonthSerializer(instance.planning_year_month).data
        response['project'] = BriefContentProjectSerializer(instance.project).data
        response['status'] = ContentStatusSerializer(instance.status).data
        response['is_late'] = instance.is_late
        return response

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related(
            'writer',
            'client',
            'poster',
            'lead',
            'editor',
            'planning_year_month',
            'project',
            'content_type',
            'status',
            'final_approver'
        )

        queryset = queryset.prefetch_related(
            'content_type',
            'contentComments',
            'writer__user',
            'keywords',
            'channels',
            # 'lead__user_preferences',
            # 'lead__user_preferences__default_organization',
            # 'editor__user_preferences',
            # 'editor__user_preferences__default_organization',
            # 'final_approver__user_preferences',
            # 'final_approver__user_preferences__default_organization',
            # 'writer__user__user_preferences',
            # 'writer__user__user_preferences__default_organization',
            # 'poster__user_preferences',
            # 'poster__user_preferences__default_organization',
            # 'client__organization_requirements',
            # 'client__org_content_requirements',
            # 'client__editorial_requirements',
            # 'client__organization_keyword_metas',
            )

        return queryset
    
    def create(self, validated_data):
        # user = self.context['request'].user
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        channels = validated_data.pop('channels')
        keywords = validated_data.pop('keywords')
        content_article = ContentArticle.objects.create(**validated_data)
        content_article.channels.set(channels)
        content_article.keywords.set(keywords)

        # if content_article.final_approver:
        #     assign_perm('view_contentarticle', content_article.final_approver, content_article)
        # if content_article.editor:
        #     assign_perm('view_contentarticle', content_article.editor, content_article)
        # if content_article.writer:
        #     assign_perm('view_contentarticle', content_article.writer.user, content_article)
        # if content_article.poster:
        #     assign_perm('view_contentarticle', content_article.poster, content_article)
        # for keyword in content_article.keywords.all():
        #     assign_perm('view_keywordmeta', content_article.writer.user, keyword)
        #     assign_perm('view_keyword', content_article.writer.user, keyword.keyword)
        #     if content_article.poster:
        #         assign_perm('view_keywordmeta', content_article.poster, keyword)
        #         assign_perm('view_keyword', content_article.poster, keyword.keyword)
        #     try:
        #         assign_perm('view_parentkeyword', content_article.writer.user, keyword.keyword.parent_keyword)
        #         if content_article.poster:
        #             assign_perm('view_parentkeyword', content_article.poster, keyword.keyword.parent_keyword)
        #     except:
        #         pass

        # for keyword in content_article.keywords.all():
        #     assign_perm('view_keywordmeta', content_article.writer.user, keyword)
        #     assign_perm('view_keyword', content_article.writer.user, keyword.keyword)
        #     try:
        #         assign_perm('view_parentkeyword', content_article.writer.user, keyword.keyword.parent_keyword)
        #     except:
        #         pass
        content_article.save()

        return content_article

    def update(self, instance, validated_data):
        # user = self.context['request'].user
        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        content_article = ContentArticle.objects.get(id=instance.id)
        channels = validated_data.pop('channels')
        keywords = validated_data.pop('keywords')
        try:
            instance = ContentArticle(date_created=instance.date_created, **validated_data)
        except:
            instance = ContentArticle(id=instance.id, date_created=instance.date_created, **validated_data)
        instance.channels.set(channels)
        instance.keywords.set(keywords)

        if content_article.google_doc:
            new_doc_url = validated_data.get('google_doc')
            if new_doc_url == None:
                instance.google_doc = content_article.google_doc

        if content_article.scheduled_date:
            new_scheduled_date = validated_data.get('scheduled_date')
            if new_scheduled_date == None:
                instance.scheduled_date = content_article.scheduled_date

        if content_article.writer_planned_duedate:
            new_writer_planned_duedate = validated_data.get('writer_planned_duedate')
            if new_writer_planned_duedate == None:
                instance.writer_planned_duedate = content_article.writer_planned_duedate

        # if instance.final_approver:
        #     assign_perm('view_contentarticle', instance.final_approver, instance)
        # if instance.editor:
        #     assign_perm('view_contentarticle', instance.editor, instance)
        # if instance.writer:
        #     assign_perm('view_contentarticle', instance.writer.user, instance)
        # if instance.poster:
        #     assign_perm('view_contentarticle', instance.poster, instance)
        # for keyword in content_article.keywords.all():
        #     assign_perm('view_keywordmeta', instance.writer.user, keyword)
        #     assign_perm('view_keyword', instance.writer.user, keyword.keyword)
        #     if instance.poster:
        #         assign_perm('view_keywordmeta', instance.poster, keyword)
        #         assign_perm('view_keyword', instance.poster, keyword.keyword)
        #     try:
        #         assign_perm('view_parentkeyword', instance.writer.user, keyword.keyword.parent_keyword)
        #         if instance.poster:
        #             assign_perm('view_parentkeyword', instance.poster, keyword.keyword.parent_keyword)
        #     except:
        #         pass
        instance.save()

        return instance
        

class ArticleTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticleTemplate
        fields = ('__all__')
        
    
    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['client'] = OrganizationSerializer(instance.client).data
        response['writer'] = WriterSerializer(instance.writer).data
        response['editor'] = QuickUserDetailsSerializer(instance.editor).data
        response['lead'] = QuickUserDetailsSerializer(instance.lead).data
        response['poster'] = QuickUserDetailsSerializer(instance.poster).data
        response['final_approver'] = QuickUserDetailsSerializer(instance.final_approver).data
        response['content_type'] = ContentTypeSerializer(instance.content_type).data
        return response

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related(
            'client', 
            'editor', 
            'writer', 
            'lead', 
            'poster', 
            'final_approver', 
            'content_type'
            )

        queryset = queryset.prefetch_related(
            'content_type',
            'writer__user',
            )

        queryset = queryset.prefetch_related(
            Prefetch('content_channels',
                     queryset=ContentChannel.objects.all())
        )

        return queryset



class InvitationReadSerializer(serializers.ModelSerializer):
    inviter = UserDetailsSerializer(read_only=True)
    organization = OrganizationSerializer(read_only=True)
    role = GroupSerializer(read_only=True)

    class Meta:
        model = InvitationModel
        fields = '__all__'

class InvitationWriteSerializer(serializers.ModelSerializer):
    key = serializers.CharField(required=False)

    class Meta:
        model = InvitationModel
        fields = (
            'email', 
            'organization', 
            'role', 
            'is_writer', 
            'price', 
            'first_name',
            'last_name',
            'title',
            'phone_number',
            'send_invite',
            'receive_reporting_email',
            'receive_approval_reminders',
            'create_user',
            'key'
            )

    def _validate_invitation(self, email):
        if InvitationModel.objects.all_valid().filter(
                email__iexact=email, accepted=False):
            raise AlreadyInvited
        elif InvitationModel.objects.filter(
                email__iexact=email, accepted=True):
            raise AlreadyAccepted
        elif get_user_model().objects.filter(email__iexact=email):
            raise UserRegisteredEmail
        else:
            return True

    def validate_email(self, email):
        email = get_invitations_adapter().clean_email(email)

        try:
            self._validate_invitation(email)
        except(AlreadyInvited):
            raise serializers.ValidationError(errors["already_invited"])
        except(AlreadyAccepted):
            raise serializers.ValidationError(errors["already_accepted"])
        except(UserRegisteredEmail):
            raise serializers.ValidationError(errors["email_in_use"])
        return email


    def create(self, validate_data):
        return InvitationModel.create(**validate_data)

class WriterContentArticleSerializer(serializers.Serializer):
    articleId = serializers.IntegerField()
    # to_status = serializers.IntegerField()
    to_status = serializers.CharField(max_length=250)
    scheduled_date = serializers.DateField(allow_null=True, required=False)
    writer_planned_duedate = serializers.DateField(allow_null=True, required=False)
    posted_url = serializers.URLField(allow_null=True, required=False)
    admin_draft_url = serializers.URLField(allow_null=True, required=False)


class CreateGoogleDocSerializer(serializers.Serializer):
    organization = serializers.CharField(max_length=250)
    year = serializers.IntegerField(allow_null=True, required=False)
    month = serializers.IntegerField(allow_null=True, required=False)
    title = serializers.CharField(max_length=255)
    articleId = serializers.IntegerField()
    projectId = serializers.IntegerField(allow_null=True, required=False)
