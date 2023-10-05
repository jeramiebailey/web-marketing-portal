from django.core.management.base import BaseCommand
import csv
from docker_drf_backend.users.models import User
from content_management.models import PlanningYearMonth, ContentType, Keyword, Organization, KeywordMeta, ContentStatus, Writer, ContentArticle
import datetime
import sys


class Command(BaseCommand):
    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('planning_year', type=int)
        parser.add_argument('planning_month', type=int)

    def handle(self, *args, **kwargs):
        planning_year = kwargs['planning_year']
        planning_month = kwargs['planning_month']

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
        try:
            index_kd = results[0].index("KD")
        except:
            index_kd = None
        index_status = results[0].index("Status")
        index_writer = results[0].index("Writer")
        try:
            index_lead = results[0].index("Lead")
        except:
            index_lead = None


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

                if index_kd:
                    try:
                        keyword = Keyword.objects.get(name=row[index_kw_1], difficulty=row[index_kd])
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
                        client = Organization.objects.get(dba_name__contains='Heat')
                    elif row[index_client] == 'DC':
                        client = Organization.objects.get(dba_name__contains='Dirt Connections')
                    elif row[index_client] == 'BE':
                        client = Organization.objects.get(dba_name__contains='Beyond')
                    elif row[index_client] == 'FMI':
                        client = Organization.objects.get(dba_name__contains='Fairfax Mortgage Investments')
                    elif row[index_client] == 'MFE':
                        client = Organization.objects.get(dba_name__contains='MFE Insurance')
                    else:
                        client = Organization.objects.get(dba_name__contains=row[index_client])
                except:
                    client = None

                if index_kd:
                    keywords, keywords_created = KeywordMeta.objects.get_or_create(keyword=keyword, organization=client)
                    try:
                        keywords.planning_months.add(planning_year_month)
                        keywords.save()
                    except:
                        pass

                status, status_created = ContentStatus.objects.get_or_create(name=row[index_status])

                try:
                    writer = Writer.objects.get(user__name__contains=row[index_writer])
                except:
                    writer = Writer.objects.get(user__username="elijah.millard")

                if index_lead:
                    try:
                        editor = User.objects.get(name__contains=row[index_lead])
                    except:
                        editor = User.objects.get(username="elijah.millard")
                else:
                    editor = None

                if index_lead:
                    try:
                        final_approver = editor
                    except:
                        final_approver = editor
                else:
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

                print(row[index_client])

                content_article = ContentArticle.objects.create(
                    planning_year_month=planning_year_month,
                    title=title,
                    description=description,
                    content_type=content_type,
                    client=client,
                    status=status,
                    writer=writer,
                    editor=editor,
                    final_approver=final_approver,
                    min_word_count=min_word_count,
                    milestone=milestone,
                    duedate_draft=duedate_draft,
                    duedate_clientreview=duedate_clientreview,
                    duedate_golive=duedate_golive,
                    url_1=url_1,
                    anchor_1=anchor_1,
                    url_2=url_2,
                    anchor_2=anchor_2,
                    archived=archived,
                )

                try:
                    content_article.keywords.add(keywords)
                except:
                    pass
                content_article.save()

            except:
                print('error')
                raise
