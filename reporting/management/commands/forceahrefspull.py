from django.core.management.base import BaseCommand, CommandError
from reporting.models import MonthlyReport
from organizations.models import Organization
from content_management.models import PlanningYearMonth
from django.db.models import Q
from dateutil.relativedelta import *
from django.utils import timezone
import datetime

class Command(BaseCommand):
    help = 'Creates and populates Content Article history set for the last three months'

    def handle(self, *args, **kwargs):
        today = datetime.datetime.today()
        today_day = today.day

        try:
            current_planning_month = PlanningYearMonth.objects.get(month=today.month, year=today.year)
        except:
            current_planning_month = None

        if current_planning_month:
            count = 0
            corresponding_reports = MonthlyReport.objects.filter(
                Q(referring_domains_screenshot__exact='') |
                Q(referring_pages_screenshot__exact='') |
                Q(organic_keywords_screenshot__exact='') |
                Q(detailed_organic_keywords_screenshot__exact=''),
                month=current_planning_month)
            print(f'corresponding_reports count was: {corresponding_reports.count()}')

            if corresponding_reports and corresponding_reports[0]:
                for report in corresponding_reports:
                    report.get_ahrefs_screenshots()
                    count += 1       

            if count and count > 0:
                self.stdout.write(self.style.SUCCESS(f'Attempted to pull Ahrefs data for {count} report(s)'))
            else:
                self.stdout.write(self.style.ERROR(f'All reports have corresponding Ahrefs data.'))
        
        else:
            self.stdout.write(self.style.ERROR(f'Could not locate the current planning month of {today.month} {today.year}'))