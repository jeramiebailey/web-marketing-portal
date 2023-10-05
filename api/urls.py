from django.conf.urls import include, url
from django.urls import path
from rest_framework import routers
from django.conf import settings
from .views import *
from docker_drf_backend.users.views import UserViewSet, PreferencesViewSet, GroupViewSet, PermissionViewSet, UserOrgRoleViewSet, MyRegisterView, UserPasswordChangeView
from user_feedback.views import UserFeedbackViewSet
from client_onboarding.views import WebsiteBuildViewSet
from reporting.views import MonthlyReportViewSet, ReportEmailEntryViewSet
from content_management.views import ArticleViewSet, FeedbackViewSet, ReassignArticles, ContentArticleHistorySetViewSet
from wp_deployments.views import InitializeWPBuild, ConfirmCompleteWPBuild, WebAppViewSet, ChildThemeViewSet, GenerateS3Download
from ui_mapping.views import UIComponentViewSet
from checklists.views import ChecklistViewSet, ChecklistTemplateViewSet, ChecklistItemViewSet, ChecklistTemplateItemViewSet, ChecklistTemplateItemAttachmentViewSet, ChecklistItemAttachmentViewSet, MasterChecklistTemplateViewSet
from presentations.views import SlideTemplateViewSet, SlideViewSet, SlideDeckViewSet, SlideDeckTemplateViewSet
from organizations.views import WhatConvertsAccountViewSet
from reporting.views import CreateMonthlyReportsView, ValidateMonthlyReportDataView, CreateReportPresentationsView, BulkMonthlyReportPresentationTemplateUpdateView, QueryUnsentReportsView
from organizations.views import OrganizationViewSet
from account_health.views import AccountHealthViewSet
from notifications.views import SystemNotificationViewSet
from rest_invitations.app_settings import ACCEPT_INVITE_URL, API_BASE_URL

frontend_url = settings.FRONTEND_URL 

router = routers.DefaultRouter()
router.register('users', UserViewSet, 'users')
router.register('user-preferences', PreferencesViewSet, 'user_preferences')
router.register('content-object-types', ContentObjectTypeViewSet, 'content_object_types')
router.register('staff', ContentStaffViewSet, 'staff')
router.register('groups', GroupViewSet, 'groups')
router.register('permissions', PermissionViewSet, 'permissions')
router.register('notifications', NotificationViewSet, 'notifications')
router.register('organizations', OrganizationViewSet, 'organizations')
router.register('whatconverts-accounts', WhatConvertsAccountViewSet, 'whatconvertsaccounts')
router.register('roles', UserOrgRoleViewSet, 'roles')
router.register('addresses', AddressViewSet)
router.register('account-health-overviews', AccountHealthViewSet, 'accounthealthoverviews')
router.register('planning-months', PlanningYearMonthViewSet, 'planning_months')
router.register('content-projects', ContentProjectViewSet, 'content_projects')
router.register('content-statuses', ContentStatusViewSet, 'content_statuses')
router.register('content-types', ContentTypeViewSet)
router.register('content-channels', ContentChannelViewSet)
router.register('content-keywords', ContentKeywordsViewSet)
router.register('content-tags', ContentTagViewSet, 'content_tags')
router.register('parent-keywords', ParentKeywordViewSet, 'parent_keywords')
router.register('keywords', KeywordViewSet, 'keywords')
router.register('keyword-metas', KeywordMetaViewSet, 'keyword_metas')
router.register('url-rankings', UrlRankingViewSet, 'url_rankings')
router.register('writers', WriterViewSet)
router.register('content-articles', ContentArticleViewSet, 'content_articles')
router.register('articles', ArticleViewSet, 'articles')
router.register('content-comments', ContentCommentsViewSet)
router.register('article-templates', ArticleTemplateViewSet, 'article_templates')
router.register('org-editorial-requirements', OrganizationEditorialRequirementViewSet)
router.register('organization-requirements', OrganizationRequirementsViewSet)
router.register('feedback', FeedbackViewSet, 'feedback')
router.register('article-history-sets', ContentArticleHistorySetViewSet, 'article_history_sets')
router.register('user-feedback', UserFeedbackViewSet, 'user_feedback')
router.register('master-checklist-templates', MasterChecklistTemplateViewSet, 'master_checklist_templates')
router.register('checklist-templates', ChecklistTemplateViewSet, 'checklist_templates')
router.register('checklist-template-items', ChecklistTemplateItemViewSet, 'checklist_template_items')
router.register('checklists', ChecklistViewSet, 'checklists')
router.register('checklist-items', ChecklistItemViewSet, 'checklist_items')
router.register('checklist-template-item-attachments', ChecklistTemplateItemAttachmentViewSet, 'checklist_template_item_attachments')
router.register('checklist-item-attachments', ChecklistItemAttachmentViewSet, 'checklist_item_attachments')
router.register('website-builds', WebsiteBuildViewSet, 'website_builds')
router.register('web-applications', WebAppViewSet, 'web_applications')
router.register('wp-child-themes', ChildThemeViewSet, 'wp_child_themes')
router.register('monthly-reports', MonthlyReportViewSet, 'monthly_reports')
router.register('report-email-entries', ReportEmailEntryViewSet, 'report_email_entries')
router.register('slide-decks', SlideDeckViewSet, 'slide_decks')
router.register('slide-deck-templates', SlideDeckTemplateViewSet, 'slide_decks_templates')
router.register('slides', SlideViewSet, 'slides')
router.register('slide-templates', SlideTemplateViewSet, 'slide_templates')
router.register('ui-components', UIComponentViewSet, 'ui_components')
router.register('system-notifications', SystemNotificationViewSet, 'system_notifications')
#router.register('master-checklist-templates', MasterChecklistTemplateViewSet, 'master_checklist_templates')
router.register(r'{0}'.format(API_BASE_URL), InvitationViewSet)

app_name = "api"
urlpatterns = [
    url("^", include(router.urls)),
    # url(r'^', include('django.contrib.auth.urls')),
    url(r'^rest-auth/', include('rest_auth.urls')),
    url(r'^rest-auth/registration/$', MyRegisterView.as_view(), name='rest_register'),
    url(r'^rest-auth/registration/', include('rest_auth.registration.urls')),
    url(
            r'^{0}/{1}/(?P<key>\w+)/?$'.format(
                API_BASE_URL, ACCEPT_INVITE_URL
            ),
            accept_invitation,
            name='accept-invite'
        ),
    url(r'^submit-article/', UpdateArticleStatus.as_view(), name="submit_article"),
    url(r'^reassign-articles/', ReassignArticles.as_view(), name="reassign_articles"),
    url(r'^create-google-doc/', CreateGoogleDocView.as_view(), name="create_google_doc"),
    url(r'^initialize-website/', InitializeWPBuild.as_view(), name="initialize_website"),
    url(r'^initialization-success/', ConfirmCompleteWPBuild.as_view(), name="initialize_success"),
    url(r'^generate-s3-download/', GenerateS3Download.as_view(), name="generate_s3_download"),
    path('change-user-password/', UserPasswordChangeView.as_view(), name="change_user_password"),
    path('create-monthly-reports/', CreateMonthlyReportsView.as_view(), name="create_monthly_reports"),
    path('validate-monthly-report-data/', ValidateMonthlyReportDataView.as_view(), name="validate_monthly_report_data"),
    path('create-monthly-report-presentations/', CreateReportPresentationsView.as_view(), name="create_monthly_report_presentations"),
    path('recreate-report-templates-from-master/', BulkMonthlyReportPresentationTemplateUpdateView.as_view(), name="recreate_report_templates_from_master"),
    path('query-unsent-reports/', QueryUnsentReportsView.as_view(), name="query_unsent_reportd"),
    path('utilities/', include('utilities.urls')),
    # path('reporting/', include('reporting.urls')),
    url(r'^', include('rest_invitations.urls')),
]
