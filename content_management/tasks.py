from celery import shared_task
from django.apps import apps
from docker_drf_backend.taskapp.celery import app
from docker_drf_backend.users.models import User
from organizations.models import Organization
from docker_drf_backend.users.models import UserOrgRole
from content_management.models import ContentArticle, ContentStatus, ContentProject, ContentArticleHistorySet
from django.core.mail import send_mail
import datetime
import requests
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
import environ
from django.db.models import Q
from django.conf import settings
from guardian.shortcuts import assign_perm, remove_perm
from dateutil.relativedelta import *
from django.utils import timezone
from docker_drf_backend.utils import send_email

env = environ.Env()
mailgun_api_key = env('MAILGUN_API_KEY')
mailgun_domain = 'mg.321webmarketing.com'
frontend_url = settings.FRONTEND_URL 

@shared_task(name="check_posted_articles")
def check_posted_articles():
    today = datetime.datetime.today()
    # scheduled_status = ContentStatus.objects.get(order=9)
    # posted_status = ContentStatus.objects.get(order=10)
    scheduled_status = ContentStatus.objects.get(uid='scheduled')
    posted_status = ContentStatus.objects.get(uid='posted')
    scheduled_articles = ContentArticle.objects.filter(status=scheduled_status, scheduled_date__lte=today)
    for article in scheduled_articles:
        article.status = posted_status
        article.save()

@shared_task(name="check_completed_projects")
def check_completed_projects():
    active_projects = ContentProject.objects.filter(complete=False)

    for project in active_projects:
        statuses = project.get_article_statuses()
        article_count = statuses['article_count']
        live_count = statuses['live_count']

        if article_count == live_count:
            project.complete = True
            project.save()

@shared_task(name="send_weekly_review_email")
def send_weekly_review_email(organization_name):
    if organization_name:
        try:
            organizations = Organization.objects.filter(is_active=True, dba_name=organization_name)
        except:
            organizations = None
        # print(f'with org name. org is {organizations}')
    else:
        organizations = Organization.objects.filter(is_active=True)
        # print(f'without org name. orgs are {organizations}')
    if organizations:
        for organization in organizations:
                approval_staff = UserOrgRole.objects.filter(receive_approval_reminders=True, organization=organization)
                pending_articles = ContentArticle.objects.filter(client=organization, status__name="Final Review", archived=False)         

                # print(f'function fired. org is {organization.dba_name}. Pending article count is {pending_articles.count()}. org_user count is {approval_staff.count()}')

                if pending_articles.count() > 0:
                        email_context = { 
                                'organization_name': organization.dba_name,
                                'article_count': pending_articles.count(),
                                'hostname': frontend_url,
                        }
                        subject = "You have content articles awaiting your approval"
                        html = render_to_string('content_management/pending_approval_email.html', email_context)
                        from_email = '321 Portal <noreply@{0}>'.format(mailgun_domain)
                        recipient_list = [organization.business_email,]

                        for article in pending_articles:
                                article_approver = article.final_approver
                                if article_approver and article_approver.email:
                                    if article_approver.email not in recipient_list:
                                            recipient_list.append(article_approver.email)

                        for org_user in approval_staff:
                                email = org_user.user.email
                                if org_user.user and email:
                                    if email not in recipient_list:
                                            recipient_list.append(email)

                        weekly_review_email = send_mail(
                                subject=subject, 
                                message=html,
                                html_message=html, 
                                from_email=from_email, 
                                recipient_list=recipient_list
                                )
                        
                        # print(f'emails sent. Recipients are {recipient_list}')

@app.task
def assign_article_permissions(article_id):
    try:
        article = ContentArticle.objects.get(id=article_id)
    except:
        article = None

    print('assign_article_permissions article_id is: ', article_id, 'and article is: ', article)
    
    if article:
        if article.final_approver:
            assign_perm('view_contentarticle', article.final_approver, article)
            assign_perm('approve_contentarticle', article.final_approver, article)
            print('assign_article_permissions [final_approver] permissions assigned')
        if article.editor:
            assign_perm('view_contentarticle', article.editor, article)
            assign_perm('edit_contentarticle', article.editor, article)
            print('assign_article_permissions [editor] permissions assigned')
        if article.writer:
            assign_perm('view_contentarticle', article.writer.user, article)
            assign_perm('write_contentarticle', article.writer.user, article)
            print('assign_article_permissions [writer] permissions assigned')
        if article.poster:
            assign_perm('view_contentarticle', article.poster, article)
            print('assign_article_permissions [poster] permissions assigned')

        for keyword in article.keywords.all():
            if article.writer:
                assign_perm('view_keywordmeta', article.writer.user, keyword)
                assign_perm('view_keyword', article.writer.user, keyword.keyword)
                print('assign_article_permissions [writer.user] keyword permissions assigned')
            if article.poster:
                assign_perm('view_keywordmeta', article.poster, keyword)
                assign_perm('view_keyword', article.poster, keyword.keyword)
                print('assign_article_permissions [writer.poster] keyword permissions assigned')
            try:
                assign_perm('view_parentkeyword', article.writer.user, keyword.keyword.parent_keyword)
                if article.poster:
                    assign_perm('view_parentkeyword', article.poster, keyword.keyword.parent_keyword)
                    print('assign_article_permissions [subkeywords] keyword permissions assigned')
            except:
                pass

        # for keyword in article.keywords.all():
        #     assign_perm('view_keywordmeta', article.writer.user, keyword)
        #     assign_perm('view_keyword', article.writer.user, keyword.keyword)
        #     print('assign_article_permissions [] permissions assigned')
        #     try:
        #         assign_perm('view_parentkeyword', article.writer.user, keyword.keyword.parent_keyword)
        #         print('assign_article_permissions [] permissions assigned')
        #     except:
        #         pass

@app.task
def assign_user_article_permissions(user_id):
    try:
        user = User.objects.get(id=user_id)
    except:
        user = None

    if user:
        org_roles = user.org_roles.all()

        if org_roles:
            for role in org_roles:
                organization = role.organization
                if organization:
                    
                    organization_articles = ContentArticle.objects.select_related('client', 'writer', 'poster', 'final_approver', 'editor').filter(client=organization)
                    assign_perm('view_contentarticle', user, organization_articles)


@app.task
def cascade_article_templates(planning_year_month_id):
    PlanningYearMonth = apps.get_model(app_label='content_management', model_name='PlanningYearMonth')
    ArticleTemplate = apps.get_model(app_label='content_management', model_name='ArticleTemplate')
    ContentStatus = apps.get_model(app_label='content_management', model_name='ContentStatus')
    ContentArticle = apps.get_model(app_label='content_management', model_name='ContentArticle')
    created_count = 0

    try:
        created_planning_month = PlanningYearMonth.objects.get(id=planning_year_month_id)
    except:
        created_planning_month = None
        
    article_templates = ArticleTemplate.objects.filter(archived=False)

    try:
        # backlog = ContentStatus.objects.get(order=1)
        backlog = ContentStatus.objects.get(uid='backlog')
    except:
        backlog = None

    if created_planning_month:
        for template in article_templates:
            # Establish duedate_write based off of milestone
            if template.milestone == 1 or template.milestone == '1':
                duedate_write = created_planning_month.default_milestone_one
            elif template.milestone == 2 or template.milestone == '2':
                duedate_write = created_planning_month.default_milestone_two
            else:
                duedate_write = None

            # Establish editor due date offset
            if created_planning_month.editor_due_date_offset:
                editing_due_date_offset = created_planning_month.editor_due_date_offset
            else:
                editing_due_date_offset = 14

            # Establish duedate_edit and duedate_golive
            if duedate_write:
                duedate_edit = duedate_write + datetime.timedelta(days=editing_due_date_offset)
                duedate_golive = duedate_write + relativedelta(weeks=3)
            else:
                duedate_write = None
                duedate_edit = None
                duedate_golive = None

            # Create new article based off of respective template with due dates
            new_article = ContentArticle.objects.create(
                title=template.title,
                planning_year_month=created_planning_month,
                content_type=template.content_type,
                client=template.client,
                writer=template.writer,
                editor=template.editor,
                lead=template.lead,
                poster=template.poster,
                final_approver=template.final_approver,
                min_word_count=template.min_word_count,
                milestone=template.milestone,
                status=backlog,
                duedate_write = duedate_write,
                duedate_edit = duedate_edit,
                duedate_golive = duedate_golive
            )
            new_article.save()
            new_article.channels.set(template.content_channels.all())
            new_article.save()

            assign_article_permissions.delay(article_id=new_article.id)
            created_count += 1

        if created_count > 0:
            return f'Created {created_count} New Articles'
        else:
            return 'No new articles were created'
    else:
        return None


@shared_task(name="populate_daily_article_history_set")
def populate_daily_article_history_set():
    # due_date_required_status_orders = [3, 4, 5, 6, 7, 8]
    # due_date_required_statuses = ['writing', 'rewrite', 'editing', 'reedit', 'final_review', 'ready_to_post', 'post_qa']
    # statuses = ContentStatus.objects.filter(uid__in=due_date_required_statuses)
    statuses = ContentStatus.objects.filter(status_type='Active')
    now = timezone.now()
    created_history_sets = []

    for status in statuses:
        try:
            new_article_history_set = ContentArticleHistorySet.objects.create(as_of_date=now, status=status)
            print('found new_article_history_set running populate_daily_article_history_set')
        except:
            new_article_history_set = None
            print('DID NOT find new_article_history_set running populate_daily_article_history_set')

        if new_article_history_set:
            created_history_sets.append(new_article_history_set)
    
    if created_history_sets and created_history_sets[0]:
        resp = f'Created {len(created_history_sets)} new history sets'
    else:
        resp = 'No new history sets created'

    print(resp)

@shared_task(name="populate_weekly_article_history_set")
def populate_weekly_article_history_set():
    today = datetime.datetime.today()
    this_year = int(today.strftime("%Y"))
    this_month = int(today.strftime("%m"))
    this_day = int(today.strftime("%d"))
    start_date = datetime.datetime(this_year, this_month, this_day)
    # target_statuses = [2, 3, 4, 5, 6, 7, 8]
    # target_statuses = ['planned', 'writing', 'rewrite', 'editing', 'reedit', 'final_review', 'ready_to_post', 'post_qa']
    target_statuses = ContentStatus.objects.filter(status_type='Active')

    for target_status in target_statuses:
        target_date = start_date + relativedelta(weeks=-1)
        target_date_year = int(target_date.strftime("%Y"))
        target_date_month = int(target_date.strftime("%m"))
        target_date_day = int(target_date.strftime("%d"))

        try:
            created_article_history_set = ContentArticleHistorySet.objects.create(
                    status=target_status,
                    year=target_date_year, 
                    month=target_date_month, 
                    day=target_date_day
                )
        except:
            created_article_history_set = None

@shared_task(name="send_due_soon_reminders")
def send_due_soon_reminders():
    all_users = User.objects.filter(is_active=True)
    for user in all_users:
        due_soon_assignments = user.get_due_soon_assignments(days_out=2)
        if due_soon_assignments and due_soon_assignments.first() and user.email:
            template = 'content_management/due_soon_reminder.html'
            subject = f"[321 Portal] You have assignments that are due soon."
            email_context = { 
                "count": due_soon_assignments.count(),
                'assignments': due_soon_assignments,
                "statuses": {
                    "Planned": due_soon_assignments.filter(status__uid="planned"),
                    "Writing": due_soon_assignments.filter(status__uid="writing"),
                    "Re-write": due_soon_assignments.filter(status__uid="rewrite"),
                    "Editing": due_soon_assignments.filter(status__uid="editing"),
                    "Re-edit": due_soon_assignments.filter(status__uid="reedit"),
                    "Final_review": due_soon_assignments.filter(status__uid="final_review"),
                    "Post QA": due_soon_assignments.filter(status__uid="post_qa"),
                    "Ready to Post": due_soon_assignments.filter(status__uid="ready_to_post"),
                },
                "hostname": frontend_url,
            }

            recipient_list = [user.email,]

            due_soon_reminder_email = send_email(
                                    template=template,
                                    recipients=recipient_list,
                                    subject=subject,
                                    context=email_context,
                                )