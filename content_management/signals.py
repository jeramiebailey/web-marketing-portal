from .models import ContentStatus, PlanningYearMonth, ContentArticle, Feedback, ContentArticleHistorySet
from docker_drf_backend.users.models import UserOrgRole
from django.db.models.signals import post_save, post_delete, pre_save
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from guardian.shortcuts import assign_perm, remove_perm
from django.db import transaction
import calendar
import datetime
import environ
from django.core.mail import send_mail
from django.db.models import Q
from django.conf import settings
from django.template.loader import render_to_string
from content_management.tasks import assign_article_permissions
from dateutil.relativedelta import *
from django.utils import timezone
from docker_drf_backend.utils import send_email

env = environ.Env()
mailgun_api_key = env('MAILGUN_API_KEY')
mailgun_domain = 'mg.321webmarketing.com'
frontend_url = settings.FRONTEND_URL

@receiver(pre_save, sender=PlanningYearMonth)
def assign_default_milestones(sender, instance, **kwargs):
    # print('working')
    if getattr(instance, 'default_status', None) is None:
        instance.default_status = ContentStatus.objects.first().pk
    # if(instance.year is not None and instance.month is not None):
    #     print('is not')
    #     if getattr(instance, 'default_milestone_one', None) is None:
    #         instance.default_milestone_one = datetime.datetime(instance.year, instance.month, 15, 00, 00)
    #     if getattr(instance, 'default_milestone_two', None) is None:
    #         last_day = calendar.monthrange(instance.year, instance.month)[1]
    #         instance.default_milestone_two = datetime.datetime(instance.year, instance.month, last_day, 00, 00)


@receiver(post_save, sender=Feedback)
def assign_feedback_perms(sender, created, instance, **kwargs):
    article = instance.article
    if created:
        if article:
            try:
                assign_perm('view_feedback', article.writer.user, instance)
            except:
                pass
            try:
                assign_perm('view_feedback', article.editor, instance)
            except:
                pass
            try:
                assign_perm('view_feedback', article.poster, instance)
            except:
                pass
            try:
                assign_perm('view_feedback', article.final_approver, instance)
            except:
                pass
            try:
                assign_perm('view_feedback', article.lead, instance)
            except:
                pass


@receiver(post_save, sender=ContentArticle)
def assign_default_milestones(sender, created, instance, **kwargs):
    if getattr(instance, 'status', None) is None and getattr(instance, 'planning_year_month', None) is not None:
        instance.status = instance.planning_year_month.default_status

@receiver(post_save, sender=ContentArticle)
def assign_corresponding_article_perms(sender, created, instance, **kwargs):
    if not created:
        # assigned_perms = assign_article_permissions(instance.id)
        assigned_perms = assign_article_permissions.delay(instance.id)

@receiver(pre_save, sender=ContentArticle)
def populate_corresponding_due_dates(sender, instance, **kwargs):
    now = timezone.now()
    today = datetime.date.today()
    next_week = today + relativedelta(weeks=1)
    next_week_datetime = now + relativedelta(weeks=1)

    try:
        old_instance = ContentArticle.objects.get(id=instance.id)
    except:
        old_instance = None

    if old_instance: 
        previous_status = getattr(old_instance, 'status', None)
        new_status = getattr(instance, 'status', None) 
        
        duedate_write = getattr(instance, 'duedate_write', None)
        duedate_rewrite = getattr(instance, 'duedate_rewrite', None)
        duedate_edit = getattr(instance, 'duedate_edit', None)
        duedate_reedit = getattr(instance, 'duedate_reedit', None)
        duedate_finalreview = getattr(instance, 'duedate_finalreview', None)
        duedate_qapost = getattr(instance, 'duedate_qapost', None)
        duedate_schedulepost = getattr(instance, 'duedate_schedulepost', None)
        duedate_golive = getattr(instance, 'duedate_golive', None)
        
        if previous_status and new_status and previous_status.uid != new_status.uid:
            
            
            # if article went to re-write
            if new_status.uid == 'rewrite':
                instance.duedate_rewrite = next_week
            # if article went to re-edit
            if new_status.uid == 'reedit':
                instance.duedate_reedit = next_week
                
                
            # if article went to final review
            if new_status.uid == 'final_review':
                instance.duedate_finalreview = next_week
            # if article went to ready to post
            if new_status.uid == 'ready_to_post':
                instance.duedate_schedulepost = next_week_datetime
            if new_status.uid == 'post_qa':
                instance.duedate_qapost = today + relativedelta(days=3)





@receiver(post_save, sender=Feedback)
def rejected_feedback_email(sender, created, instance, **kwargs):
    # print(f'instance approved status is {instance.approved}')
    if instance.approved == False:
        rejector = instance.given_by.name
        satisfaction = instance.satisfaction
        # planning_month = instance.article.planning_year_month
        # project = instance.project
        feedback_body = instance.feedback_body
        date_created = instance.date_created
        article = instance.article
        rejected_count = Feedback.objects.filter(article=instance.article).count()
        
        try:
            editor_email = article.editor.email
        except:
            # editor_email = None
             editor_email = None

        if article:
            if article.planning_year_month:
                month_project = article.planning_year_month
            elif article.project:
                month_project = article.project
        else:
            month_project = None

        # print(f'function fired, satisfaction is {satisfaction}, editor email is {editor_email}')

        email_context = { 
                "article_name": article.title,
                "client": article.client.dba_name,
                "rejector": rejector,
                "satisfaction": satisfaction,
                "feedback_body": feedback_body,
                "date_created": date_created,
                "editor_email": editor_email,
                "rejected_count": rejected_count,
                "month_project": month_project,
                "hostname": frontend_url,
        }

        subject = f"[321 Portal] Rejected Article: {article.title} from {article.client.dba_name}"
        html = render_to_string('content_management/rejected_feedback_email.html', email_context)
        from_email = '321 Portal <noreply@{0}>'.format(mailgun_domain)
        recipient_list = ['elijah@321webmarketing.com', 'david.le@321webmarketing.com', 'contentgen@321webmarketing.com',]
        if editor_email:
            recipient_list += [editor_email]

        feedback_email = send_mail(
                subject=subject, 
                message=html,
                html_message=html, 
                from_email=from_email, 
                recipient_list=recipient_list
                )



@receiver(pre_save, sender=ContentArticle)
def send_approval_notice(sender, instance, **kwargs):
    try:
        old_instance = ContentArticle.objects.get(id=instance.id)
    except:
        old_instance = None

    if old_instance:
        if old_instance.status != instance.status:
            if instance.status.name == "Final Review":
                if instance.final_approver:
                    approver_email = instance.final_approver.email
                    instance_organization = instance.client
                    planning_month = instance.planning_year_month
                    project = instance.project

                    if instance_organization:
                        approval_staff = UserOrgRole.objects.filter(receive_approval_reminders=True, organization=instance_organization)

                    if planning_month:
                        month_project = planning_month
                    elif project:
                        month_project = project
                    else:
                        month_project = None

                    if not instance.final_approver.is_staff:
                        email_context = { 
                                "article_name": instance.title,
                                "client": instance.client.dba_name,
                                "month_project": month_project,
                                "hostname": frontend_url,
                        }

                        subject = f"[321 Portal] You have a new article to approve"
                        html = render_to_string('content_management/approval_notice.html', email_context)
                        from_email = '321 Portal <noreply@{0}>'.format(mailgun_domain)
                        recipient_list = [approver_email,]

                        if approval_staff:
                            for org_user in approval_staff:
                                user_email = org_user.user.email
                                if user_email not in recipient_list:
                                    recipient_list.append(user_email)

                        feedback_email = send_mail(
                                subject=subject, 
                                message=html,
                                html_message=html, 
                                from_email=from_email, 
                                recipient_list=recipient_list
                                )

@receiver(pre_save, sender=ContentArticle)
def send_writer_notice(sender, instance, **kwargs):
    try:
        old_instance = ContentArticle.objects.get(id=instance.id)
    except:
        old_instance = None

    if old_instance:
        if old_instance.status != instance.status:
            if instance.status.name == "Assigned" or instance.status.name == "Rewrite":
                if instance.writer:
                    writer_email = instance.writer.user.email
                    instance_organization = instance.client
                    planning_month = instance.planning_year_month
                    project = instance.project
                    
                    if instance.status.name == "Assigned":
                        template = 'content_management/writer_notice.html'
                        subject = f"[321 Portal] You have a new article to write"
                    else:
                        template = 'content_management/writer_rewrite_notice.html'
                        subject = f"[321 Portal] You have a new article to re-write"

                    if not instance.writer.user.is_staff:
                        email_context = { 
                                "article_name": instance.title,
                                "client": instance.client.dba_name,
                                "hostname": frontend_url,
                        }

                        recipient_list = [writer_email,]

                        writer_email_sent = reporting_email = send_email.delay(
                                    template=template,
                                    recipients=recipient_list,
                                    subject=subject,
                                    context=email_context,
                                )

@receiver(pre_save, sender=ContentArticle)
def send_editor_notice(sender, instance, **kwargs):
    try:
        old_instance = ContentArticle.objects.get(id=instance.id)
    except:
        old_instance = None

    if old_instance:
        if old_instance.status != instance.status:
            if instance.status.name == "Editing" or instance.status.name == "Re-Edit":
                if instance.editor:
                    editor_email = instance.editor.email
                    instance_organization = instance.client
                    planning_month = instance.planning_year_month
                    project = instance.project

                    if instance.status.name == "Editing":
                        template = 'content_management/editor_notice.html'
                        subject = f"[321 Portal] You have a new article to edit"
                    else:
                        template = 'content_management/editor_reedit_notice.html'
                        subject = f"[321 Portal] You have a new article to re-edit"

                    if not instance.editor.is_staff:
                        email_context = { 
                                "article_name": instance.title,
                                "client": instance.client.dba_name,
                                "hostname": frontend_url,
                        }

                        recipient_list = [editor_email,]

                        editor_email_sent = reporting_email = send_email.delay(
                                    template=template,
                                    recipients=recipient_list,
                                    subject=subject,
                                    context=email_context,
                                )


@receiver(post_save, sender=ContentArticleHistorySet)
def populate_article_history_set(sender, created, instance, **kwargs):
    if created:
        instance.populate_set(delay=False)