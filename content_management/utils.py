from docker_drf_backend.users.models import User
from django.apps import apps
from docker_drf_backend.taskapp.celery import app
from dateutil.relativedelta import *
from django.utils import timezone
import datetime

@app.task
def populate_article_history_set(article_history_set_id, fromHistory=False):
    ContentArticle = apps.get_model(app_label='content_management', model_name='ContentArticle')
    ContentArticleHistorySet = apps.get_model(app_label='content_management', model_name='ContentArticleHistorySet')
    ContentStatus = apps.get_model(app_label='content_management', model_name='ContentStatus')

    try:
        article_history_set = ContentArticleHistorySet.objects.get(id=article_history_set_id) 
    except:
        article_history_set = None

    if article_history_set:
        incomplete_status = article_history_set.status
        incomplete_status_order = article_history_set.status.order
        complete_status_order = incomplete_status_order + 1
        complete_status = ContentStatus.objects.get(order=complete_status_order)
        incomplete_count = 0 
        complete_count = 0
        late_count = 0
        no_count = 0
        now = timezone.now()
        today = datetime.datetime.today()

        previous_week = article_history_set.as_of_date + relativedelta(weeks=-1)
        previous_week_converted = datetime.datetime(previous_week.year, previous_week.month, previous_week.day).date()
        
        # previous_month = today + relativedelta(months=-1)
        previous_month = article_history_set.as_of_date + relativedelta(months=-1)
        previous_month_converted = datetime.datetime(previous_month.year, previous_month.month, previous_month.day).date()
        
        articles = ContentArticle.objects.select_related(
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
            ).prefetch_related(
                'content_type',
                'contentComments',
                'writer__user',
                'keywords',
                'channels'
            ).filter(archived=False)

        if fromHistory:
            article_set = articles.as_of(article_history_set.as_of_date)
            print('pulling fromHistory')
        else:
            article_set = articles
            print('pulling NOT fromHistory')

        for article in article_set:
            # Check the article to see if the status is equal to the current ArticleHistorySet
            if article.status:
                if article.status.order == incomplete_status_order:
                    # Check to see if the article status has an applicable duedate to perform late logic
                    if article.duedate_write or article.duedate_edit or article.duedate_schedulepost:
        
                        # Assigned status check
                        if incomplete_status.uid == 'writing' and article.duedate_write:
                            if article.duedate_write < today.date():
                                late_count += 1
                            else:
                                incomplete_count += 1

                        # Re-write status check
                        elif incomplete_status.uid == 'rewrite' and article.duedate_rewrite:
                            if article.duedate_rewrite < today.date():
                                late_count += 1
                            else:
                                incomplete_count += 1

                        # Editing status check
                        elif incomplete_status.uid == 'editing' and article.duedate_edit:
                            if article.duedate_edit < today.date():
                                late_count += 1
                            else:
                                incomplete_count += 1
                        
                        # Re-edit status check
                        elif incomplete_status.uid == 'reedit' and article.duedate_reedit:
                            if article.duedate_reedit < today.date():
                                late_count += 1
                            else:
                                incomplete_count += 1

                        # Final Review status check
                        elif incomplete_status.uid == 'final_review' and article.duedate_finalreview:

                            # Only count it if we are the final approver
                            should_count = False
                            if article.final_approver:
                                if article.final_approver.is_staff:
                                    should_count = True

                            if should_count == False:
                                no_count += 1
                            elif article.duedate_finalreview < today.date():
                                late_count += 1
                            else:
                                incomplete_count += 1

                        # Posted status check
                        elif incomplete_status.uid == 'ready_to_post' and article.duedate_schedulepost:
                            if article.duedate_schedulepost:
                                duedate_schedulepost = datetime.datetime.combine(article.duedate_schedulepost, datetime.time(17,0))
                                duedate_schedulepost = timezone.make_aware(duedate_schedulepost)
                            else:
                                duedate_schedulepost = None

                            # Only count if the type is not Press Release
                            should_count = True
                            # Commenting this out because we're counting PRs now
                            # if article.content_type:
                            #     if article.content_type.name == 'Press Release':
                            #         should_count = False

                            if should_count == False:
                                no_count += 1
                            elif duedate_schedulepost < now:
                                late_count += 1
                            else: 
                                incomplete_count += 1
                        
                        # Post QA status check
                        elif incomplete_status.uid == 'post_qa' and article.duedate_qapost:

                            if article.duedate_qapost < today.date():
                                late_count += 1
                            else:
                                incomplete_count += 1

                        else:
                            incomplete_count += 1

                    # Else it is incomplete
                    else:
                        incomplete_count += 1

                # Else if the article's status is greater than the current ArticleHistorySet
                elif article.status.order >= complete_status_order:
                    # Start Here
                    if article.duedate_write or article.duedate_edit or article.duedate_schedulepost:
            
                        # Assigned status check
                        if complete_status.uid == 'writing' and article.duedate_write:
                            if article.duedate_write < today.date() and article.duedate_write > previous_month_converted:
                                complete_count += 1

                        # Re-write status check
                        elif complete_status.uid == 'rewrite' and article.duedate_rewrite:
                            if article.duedate_rewrite < today.date() and article.duedate_rewrite > previous_month_converted:
                                complete_count += 1

                        # Editing status check
                        elif complete_status.uid == 'editing' and article.duedate_edit:
                            if article.duedate_edit < today.date() and article.duedate_edit > previous_month_converted:
                                complete_count += 1
                        
                        # Re-edit status check
                        elif complete_status.uid == 'reedit' and article.duedate_reedit:
                            if article.duedate_reedit < today.date() and article.duedate_reedit > previous_month_converted:
                                complete_count += 1

                        # Final Review status check
                        elif complete_status.uid == 'final_review' and article.duedate_finalreview:
                            if article.duedate_finalreview < today.date() and article.duedate_finalreview > previous_month_converted:
                                print(f'article.duedate_finalreview is: {article.duedate_finalreview}. previous_month_converted is: {previous_month_converted}')
                                complete_count += 1

                        # Posted status check
                        elif complete_status.uid == 'ready_to_post' and article.duedate_schedulepost:
                            if article.duedate_schedulepost:
                                duedate_schedulepost = datetime.datetime.combine(article.duedate_schedulepost, datetime.time(17,0))
                                duedate_schedulepost = timezone.make_aware(duedate_schedulepost)
                            else:
                                duedate_schedulepost = None
                                
                            if duedate_schedulepost < now and duedate_schedulepost and duedate_schedulepost > previous_month:
                                complete_count += 1

                        
                        # Post QA status check
                        elif complete_status.uid == 'post_qa' and article.duedate_qapost:
                            if article.duedate_qapost < today.date() and article.duedate_qapost > previous_month_converted:
                                complete_count += 1
                        
            else:
                print('did not find status for article with ID of: {article.id}')
                # complete_count += 1

        print(f'populate_article_history_set incomplete_count is {incomplete_count}')
        print(f'populate_article_history_set incomplete_count is {complete_count}')
        print(f'populate_article_history_set incomplete_count is {late_count}')
        article_history_set.incomplete_count = incomplete_count
        article_history_set.complete_count = complete_count
        article_history_set.late_count = late_count
        article_history_set.save()

        return {
            'incomplete_count': incomplete_count,
            'complete_count': complete_count,
            'late_count': late_count,
        }

def reassign_articles(prevUserId, newUserId):
    ContentArticle = apps.get_model(app_label='content_management', model_name='ContentArticle')
    Writer = apps.get_model(app_label='content_management', model_name='Writer')
    ArticleTemplate = apps.get_model(app_label='content_management', model_name='ArticleTemplate')
    print(f'hit the reassign_articles function. prevUserId is: {prevUserId} and newUserId is: {newUserId}')
    try:
        prevUser = User.objects.get(id=prevUserId)
    except:
        prevUser = None

    try:
        newUser = User.objects.get(id=newUserId)
    except:
        newUser = None

    print(f'pre eval prevUser is: {prevUser}, newUser is {newUser}')
    if prevUser and newUser:
        print(f'evaled successfully. prevUser is: {prevUser}, newUser is {newUser}')
        try:
            prevUserWriter = Writer.objects.get(user=prevUser)
        except:
            prevUserWriter = None
        
        try:
            newUserWriter = Writer.objects.get(user=newUser)
        except:
            newUserWriter = None

        # Get all corresponding content article templates
        filtered_article_templates = ArticleTemplate.objects.select_related(
            'client',
            'writer',
            'editor',
            'lead',
            'poster',
            'final_approver',
            'content_type',
        ).filter(archived=False)
        prevEditingTemplates = filtered_article_templates.filter(editor=prevUser)
        prevPostingTemplates = filtered_article_templates.filter(poster=prevUser)
        prevApprovingTemplates = filtered_article_templates.filter(final_approver=prevUser)
        prevLeadingTemplates = filtered_article_templates.filter(lead=prevUser)

        templates_to_update = prevEditingTemplates.count() + prevPostingTemplates.count() + prevApprovingTemplates.count() + prevLeadingTemplates.count()

        # Get all corresponding content articles
        filtered_content_articles = ContentArticle.objects.select_related(
            'client',
            'writer',
            'editor',
            'lead',
            'poster',
            'final_approver',
            'content_type',
        ).filter(archived=False)
        prevEditingArticles = filtered_content_articles.filter(editor=prevUser)
        prevPostingArticles = filtered_content_articles.filter(poster=prevUser)
        prevApprovingArticles = filtered_content_articles.filter(final_approver=prevUser)
        prevLeadingArticles = filtered_content_articles.filter(lead=prevUser)

        articles_to_update = prevEditingArticles.count() + prevPostingArticles.count() + prevApprovingArticles.count() + prevLeadingArticles.count()

        # Update all corresponding article templates
        prevEditingTemplates.update(editor=newUser)
        prevPostingTemplates.update(poster=newUser)
        prevApprovingTemplates.update(final_approver=newUser)
        prevLeadingTemplates.update(lead=newUser)

        # Update all corresponding content articles
        prevEditingArticles.update(editor=newUser)
        prevPostingArticles.update(poster=newUser)
        prevApprovingArticles.update(final_approver=newUser)
        prevLeadingArticles.update(lead=newUser)
        

        if prevUserWriter and newUserWriter:
            prevWritingTemplates = filtered_article_templates.filter(writer=prevUserWriter)

            prevWritingTemplates.update(writer=newUserWriter)

            templates_to_update = templates_to_update + prevWritingTemplates.count()

        if prevUserWriter and newUserWriter:
            prevWritingArticles = filtered_content_articles.filter(writer=prevUserWriter)

            prevWritingArticles.update(writer=newUserWriter)

            articles_to_update = articles_to_update + prevWritingArticles.count()

        resp = {
                "message": "Content Articles Successfully Re-Assigned",
                "template_update_count": templates_to_update,
                "article_update_count": articles_to_update,
                }

        print(resp)

        return resp

# def clean_deactivated_user_content(user, new_user):
#     # get deactivated user
#     karina = User.objects.get(username="karina.nyman")
#     # get new user
#     brendan = User.objects.get(username="brendan.bockes")
#     # get new user writer object if applicable
#     brendan_writer = Writer.objects.get(user=brendan)

#     # find all applicable articles
#     posting = ContentArticle.objects.filter(status__lte=9, poster=karina)
#     writing = ContentArticle.objects.filter(status__lte=9, writer__user=karina)
#     editing = ContentArticle.objects.filter(status__lte=9, editor=karina)
#     approving = ContentArticle.objects.filter(status__lte=9, final_approver=karina)
#     lead = ContentArticle.objects.filter(status__lte=9, lead=karina)

#     print(f'posting count is {posting.count()}')
#     print(f'writing count is {writing.count()}')
#     print(f'editing count is {editing.count()}')
#     print(f'approving count is {approving.count()}')
#     print(f'lead count is {lead.count()}')

#     # loop through and re-assign roles
#     for article in posting:
#         article.poster = brendan
#         article.save()
#         print(f'poster successfully assigned')
#     for article in writing:
#         article.writer = brendan_writer
#         article.save()
#         print(f'writer successfully assigned')
#     for article in editing:
#         article.editor = brendan
#         article.save()
#         print(f'editor successfully assigned')
#     for article in approving:
#         article.final_approver = brendan
#         article.save()
#         print(f'final_approver successfully assigned')
#     for article in lead:
#         article.lead = brendan
#         article.save()
#         print(f'lead successfully assigned')