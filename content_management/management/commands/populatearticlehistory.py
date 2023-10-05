from django.core.management.base import BaseCommand, CommandError
from content_management.models import ContentArticleHistorySet, ContentStatus
from dateutil.relativedelta import *
from django.utils import timezone
import datetime

class Command(BaseCommand):
    help = 'Creates and populates Content Article history set for the last three months'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        today = datetime.datetime.today()
        this_week_monday = now + relativedelta(weekday=MO(-1), hour=8)
        this_year = int(this_week_monday.strftime("%Y"))
        this_month = int(this_week_monday.strftime("%m"))
        this_day = int(this_week_monday.strftime("%d"))
        start_date = datetime.datetime(this_year, this_month, this_day)

        # target_statuses = [2, 3, 4, 5, 6, 7, 8]
        # target_statuses = ['planned', 'write', 'rewrite', 'editing', 'reedit', 'final_review', 'ready_to_post', 'post_qa']
        target_statuses = ContentStatus.objects.filter(status_type='Active')
        
        
        for status in target_statuses:
            week_count = 0
            # try:
            #     target_status = ContentStatus.objects.get(uid=status)
            # except:
            #     target_status = None

            if status:
                while week_count < 12:
                    if week_count == 0:
                        target_date = start_date
                    else:
                        target_date = start_date + relativedelta(weeks=-week_count)
                    target_date_year = int(target_date.strftime("%Y"))
                    target_date_month = int(target_date.strftime("%m"))
                    target_date_day = int(target_date.strftime("%d"))

                    created_article_history_set, created = ContentArticleHistorySet.objects.get_or_create(
                                status=status,
                                year=target_date_year, 
                                month=target_date_month, 
                                day=target_date_day
                            )
                    if not created:
                        created_article_history_set.populate_set()
                    week_count += 1

        successful = True

        if successful:
            self.stdout.write(self.style.SUCCESS(f'Successfully created {week_count} ContentArticleHistorySet objects'))
        else:
            self.stdout.write(self.style.ERROR(f'Error creating ContentArticleHistorySet objects'))