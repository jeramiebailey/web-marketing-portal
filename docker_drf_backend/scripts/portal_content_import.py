import csv
from docker_drf_backend.users.models import User
from content_management.models import PlanningYearMonth, ContentType, Keyword, Organization, KeywordMeta, ContentStatus, Writer, ContentArticle
import datetime
import sys

f = open('Content_Queue_Feb_2019.csv')
csv_f = csv.reader(f)

results = []
for row in csv_f:
    results.append(row)

index_title = results[0].index("Name")
index_client = results[0].index("Client")
index_notes = results[0].index("Notes")
index_word_count = results[0].index("Word Count")
index_milestone = results[0].index("Milestone")
index_date = results[0].index("Due Date")
index_content_type = results[0].index("Type")
index_url_1 = results[0].index("URL 1")
index_url_2 = results[0].index("URL 2")
index_kw_1 = results[0].index("Keyword 2")
index_kw_2 = results[0].index("Keyword 2")
index_kd = results[0].index("KD")
index_status = results[0].index("Status")
index_writer = results[0].index("Writer")
index_lead = results[0].index("Lead")


def find_year(date):
    year = datetime.datetime.strptime(date, "%Y-%m-%d").year
    return year

def find_month(date):
    month = datetime.datetime.strptime(date, "%Y-%m-%d").month
    return month

for row in results[1:]:
    try:
        planning_year_month, planning_year_month_created = PlanningYearMonth.objects.get_or_create(
            year=planning_year, month=planning_month)

        title = row[index_title]

        description = row[index_notes]

        try:
            content_type = ContentType.objects.get(name__contains="{0}".format(row[index_content_type]))
        except:
            content_type = None
        
        try:
            keyword, keyword_created = Keyword.objects.get_or_create(name=row[index_kw_1], difficulty=row[index_kd])
        except:
            try:
                keyword, keyword_created = Keyword.objects.get_or_create(name=row[index_kw_1])
            except:
                keyword = Keyword.objects.filter(name=row[index_kw_1]).first()

        try:
            if row[index_client] == 'BBG':
                client = Organization.objects.get(dba_name__contains='Business Benefits Group')
            elif row[index_client] == 'Green Tech Talk':
                client = Organization.objects.get(dba_name__contains='New Energy Power Systems')
            elif row[index_client] == 'SPT - CHC':
                client = Organization.objects.get(dba_name__contains='Comfort Home Care')
            elif row[index_client] == 'SPT - Presidential':
                client = Organization.objects.get(dba_name__contains='Presidential Heating & Air')
            elif row[index_client] == 'DC':
                client = Organization.objects.get(dba_name__contains='Dirt Connections')
            elif row[index_client] == 'BE':
                client = Organization.objects.get(dba_name__contains='Beyond Exteriors')
            elif row[index_client] == 'FMI':
                client = Organization.objects.get(dba_name__contains='Fairfax Mortgage Investments')
            else:
                client = Organization.objects.get(dba_name__contains=row[index_client])
        except:
            client = None

        keywords, keywords_created = KeywordMeta.objects.get_or_create(keyword=keyword, organization=client)

        status, status_created = ContentStatus.objects.get_or_create(name=row[index_status])

        try:
            writer = Writer.objects.get(user__name__contains=row[index_writer])
        except:
            writer = None

        try:
            editor = User.objects.get(name__contains=row[index_lead])
        except:
            editor = User.objects.get(name__contains=row[index_lead])

        try:
            final_approver = editor
        except:
            final_approver = None

        if row[index_word_count] == '':
            min_word_count = 0
        else:
            min_word_count = row[index_word_count]

        if row[index_milestone] == '':
            milestone = 0
        else:
            milestone = row[index_milestone]

        try:
            duedate_draft = datetime.datetime.strptime(row[index_date], "%Y-%m-%d")

            duedate_clientreview = datetime.datetime.strptime(row[index_date], "%Y-%m-%d") + datetime.timedelta(days=30)

            duedate_golive = datetime.datetime.strptime(row[index_date], "%Y-%m-%d") + datetime.timedelta(days=30)
        except:
            duedate_draft = None

            duedate_clientreview = None

            duedate_golive = None

        url_1 = row[index_url_2]

        anchor_1 = row[index_kw_2]

        url_2 = row[index_url_1]
        
        anchor_2 = row[index_kw_1]

        archived = False

        content_article = ContentArticle.objects.create(
            planning_year_month = planning_year_month,
            title = title,
            description = description,
            content_type = content_type,
            client = client,
            status = status,
            writer = writer,
            editor = editor,
            final_approver = final_approver,
            min_word_count = min_word_count,
            milestone = milestone,
            duedate_draft = duedate_draft,
            duedate_clientreview = duedate_clientreview,
            duedate_golive = duedate_golive,
            url_1 = url_1,
            anchor_1 = anchor_1,
            url_2 = url_2,
            anchor_2 = anchor_2,
            archived = archived,
        )
        
        content_article.keywords.add(keywords)
        content_article.save()

    except:
        print('error')
        raise
