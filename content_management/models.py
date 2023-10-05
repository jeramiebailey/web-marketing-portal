from django.db import models, transaction
from docker_drf_backend.users.models import User
from organizations.models import Organization
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.dates import MONTHS
from django.utils.translation import ugettext_lazy as _
from .constants import PLANNING_STATUS, PR_TYPES, VALUE_OPTIONS, MILESTONES
from django.contrib.postgres.fields import ArrayField
import datetime
import calendar
from simple_history.models import HistoricalRecords
from reporting.models import MonthlyReport
from content_management.utils import populate_article_history_set
from itertools import chain
from django.utils import timezone

def current_year():
    return datetime.date.today().year

def current_month():
    return datetime.date.today().month

def first_day_of_month():
    month_range = calendar.monthrange(current_year(), current_month())
    return month_range[0]

def last_day_of_month():
    month_range = calendar.monthrange(current_year(), current_month())
    return month_range[1]

def middle_of_month():
    return datetime.datetime(current_year(), current_month(), 15, 00, 00)

def max_value_current_year(value):
    return MaxValueValidator(current_year())(value) 

class ContentStatus(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    uid = models.CharField(max_length=100, db_index=True, unique=True, blank=True, null=True)
    status_type = models.CharField(max_length=100, null=True, blank=True)
    order = models.PositiveSmallIntegerField(unique=True, null=True, db_index=True)
    color = models.CharField(max_length=10, blank=True, default='#ffffff')
    due_date_day_offset = models.PositiveSmallIntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True, null=True)
    is_active = models.BooleanField(default=True, blank=True)

    class Meta:
        verbose_name = "Content Status"
        verbose_name_plural = "Content Status"
        permissions = (
            ('view_contentstatus__dep', 'View Content Status Deprecated'),
        )

    def __str__(self):
        return self.name

class PlanningYearMonth(models.Model):
    year = models.IntegerField(validators=[MinValueValidator(2017), MaxValueValidator(2050)], db_index=True)
    month = models.PositiveSmallIntegerField(choices=MONTHS.items(), db_index=True)
    default_milestone_one = models.DateField(null=True, blank=True)
    default_milestone_two = models.DateField(null=True, blank=True)
    editor_due_date_offset = models.PositiveSmallIntegerField(null=True, blank=True, default=14)
    article_order_array = ArrayField(models.IntegerField(), default=list, null=True, blank=True)
    default_status = models.ForeignKey(ContentStatus, related_name="related_default_months", null=True, blank=True, on_delete=models.SET_NULL)
    

    class Meta:
        unique_together = (("year", "month"))
        indexes = [
            models.Index(fields=['year', 'month']),
        ]
        verbose_name = "Planning Month"
        verbose_name_plural = "Planning Months"
        permissions = (
            ('view_planningyearmonth__dep', 'View Planning Year Month Deprecated'),
        )
        ordering = ['-year', '-month']

    def get_api_view_name(self):
        api_view_name = 'planning_months'
        return api_view_name

    def get_year_month_verbose(self):
        return f'{calendar.month_name[self.month]} {self.year}'

    def get_article_statuses(self):
        statuses = {}
        articles = ContentArticle.objects.select_related('status', 'planning_year_month').filter(archived=False, status__order__lte=10, planning_year_month=self)
        [article for article in articles]
        # statuses['article_count'] = articles.count()
        # statuses['backlog_count'] = articles.filter(status__order=1).count()
        # statuses['planned_count'] = articles.filter(status__order=2).count()
        # statuses['assigned_count'] = articles.filter(status__order__in=[3,4]).count()
        # statuses['editing_count'] = articles.filter(status__order__in=[5,6]).count()
        # statuses['final_review_count'] = articles.filter(status__order=7).count()
        # statuses['ready_to_post_count'] = articles.filter(status__order=8).count()
        # statuses['scheduled_count'] = articles.filter(status__order=9).count()
        # statuses['live_count'] = articles.filter(status__order=10).count()
        statuses['article_count'] = articles.count()
        statuses['backlog_count'] = articles.filter(status__uid='backlog').count()
        statuses['planned_count'] = articles.filter(status__uid='planned').count()
        statuses['assigned_count'] = articles.filter(status__uid__in=['writing','rewrite']).count()
        statuses['editing_count'] = articles.filter(status__uid__in=['editing','reedit']).count()
        statuses['final_review_count'] = articles.filter(status__uid='final_review').count()
        statuses['ready_to_post_count'] = articles.filter(status__uid='ready_to_post').count()
        statuses['scheduled_count'] = articles.filter(status__uid='scheduled').count()
        statuses['live_count'] = articles.filter(status__uid='posted').count()

        return statuses

    def create_monthly_reports(self, dry=False):
        all_organizations = Organization.objects.filter(is_active=True, report_required=True)
        # print(f'org count is {all_organizations.count()}')
        count = 0
        for org in all_organizations:
            try:
                creator = org.default_report_creator
            except:
                creator = None
            try:
                approver = org.default_report_approver
            except:
                approver = None

            try:
                existing_report = MonthlyReport.objects.get(
                    organization=org,
                    month=self
                )
            except:
                existing_report = None

            if not dry:
                if not existing_report:
                    new_report = MonthlyReport.objects.create(
                        organization=org,
                        month=self,
                        creator=creator,
                        approver=approver
                    )
                    new_report.save()
                    count = count + 1
        
        return f'{count} Reports Created'

            

    @transaction.atomic
    def save(self, *args, **kwargs):
        if(self.year is not None and self.month is not None):
            if getattr(self, 'default_milestone_one', None) is None:
                self.default_milestone_one = datetime.date(self.year, self.month, 15)
            if getattr(self, 'default_milestone_two', None) is None:
                last_day = calendar.monthrange(self.year, self.month)[1]
                self.default_milestone_two = datetime.date(self.year, self.month, last_day)
        super(PlanningYearMonth, self).save(*args, **kwargs)

    def __str__(self):
        return "{} {}".format(calendar.month_name[self.month], self.year)

# in progress
class ContentProject(models.Model):
    name = models.CharField(max_length=255)
    start_year = models.IntegerField(validators=[MinValueValidator(2017), MaxValueValidator(2050)], db_index=True)
    start_month = models.PositiveSmallIntegerField(choices=MONTHS.items(), db_index=True)
    due_date = models.DateField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    last_updated = models.DateTimeField(auto_now=True, null=True)
    complete = models.BooleanField(default=False, blank=True)
    history = HistoricalRecords() 
    
    class Meta:
        indexes = [
            models.Index(fields=['start_year', 'start_month']),
        ]
        verbose_name = "Content Project"
        verbose_name_plural = "Content Projects"
        permissions = (
            ('view_contentproject__dep', 'View Content Project Deprecated'),
        )
    
    def get_api_view_name(self):
        api_view_name = 'content_projects'
        return api_view_name

    def get_article_statuses(self):
        statuses = {}
        articles = ContentArticle.objects.select_related('status', 'project').filter(archived=False, status__order__lte=10, project=self)
        [article for article in articles]
        statuses['article_count'] = articles.count()
        statuses['backlog_count'] = articles.filter(status__order=1).count()
        statuses['planned_count'] = articles.filter(status__order=2).count()
        statuses['assigned_count'] = articles.filter(status__order__in=[3,4]).count()
        statuses['editing_count'] = articles.filter(status__order__in=[5,6]).count()
        statuses['final_review_count'] = articles.filter(status__order=7).count()
        statuses['ready_to_post_count'] = articles.filter(status__order=8).count()
        statuses['scheduled_count'] = articles.filter(status__order=9).count()
        statuses['live_count'] = articles.filter(status__order=10).count()

        return statuses


    def __str__(self):
        return "{}: {} {}".format(self.name, calendar.month_name[self.start_month], self.start_year)

class ContentType(models.Model):
    name = models.CharField(max_length=150)
    color = models.CharField(max_length=10, blank=True, default='#ffffff')
    last_updated = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name = "Content Type"
        verbose_name_plural = "Content Types"
        permissions = (
            ('view_contenttype__dep', 'View Content Type Deprecated'),
        )

    def __str__(self):
        return self.name

class ContentChannel(models.Model):
    name = models.CharField(max_length=150)
    default_price = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        verbose_name = "Content Channel"
        verbose_name_plural = "Content Channel"
        permissions = (
            ('view_contentchannel__dep', 'View Content Channel Deprecated'),
        )

    def __str__(self):
        return self.name

class ContentKeywords(models.Model):
    organization = models.ManyToManyField(Organization)
    name = models.CharField(max_length=200)
    volume = models.PositiveSmallIntegerField(null=True)
    difficulty = models.PositiveSmallIntegerField(null=True, blank=True)
    cost_per_click = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    created_by = models.ForeignKey(User, related_name="user_keywords", null=True, on_delete=models.SET_NULL)
    date_created = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Keyword"
        verbose_name_plural = "Keywords"
        permissions = (
            ('view_contentkeywords__dep', 'View Content Keywords Deprecated'),
        )

    def __str__(self):
        return self.name

class ContentTag(models.Model):
    name = models.CharField(max_length=200)
    created_by = models.ForeignKey(User, related_name="user_created_tags", null=True, on_delete=models.SET_NULL)
    date_created = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Content Tag"
        verbose_name_plural = "Content Tags"
        permissions = (
            ('view_contenttag__dep', 'View Content Tag Deprecated'),
        )

    def __str__(self):
        return "{}".format(self.name)

class ParentKeyword(models.Model):
    name = models.CharField(_("Parent Keyword Name"), max_length=255)
    active = models.BooleanField(default=True, blank=True)
    created_by = models.ForeignKey(User, related_name="created_parent_keywords", null=True, on_delete=models.SET_NULL)
    date_created = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Parent Keyword"
        verbose_name_plural = "Parent Keywords"
        permissions = (
            ('view_parentkeyword__dep', 'View Parent Keyword Deprecated'),
        )

    def __str__(self):
        return "{}".format(self.name)

class Keyword(models.Model):
    name = models.CharField(_("Keyword Name"), max_length=255)
    parent_keyword = models.ForeignKey(ParentKeyword, related_name="keywords", on_delete=models.SET_NULL, null=True, blank=True)
    difficulty = models.PositiveSmallIntegerField(default=1, null=True, blank=True)
    volume = models.PositiveIntegerField(default=1, null=True, blank=True)
    cost_per_click = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    active = models.BooleanField(default=True, blank=True)
    created_by = models.ForeignKey(User, related_name="created_keywords", null=True, on_delete=models.SET_NULL)
    date_created = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Keyword"
        verbose_name_plural = "Keywords"
        permissions = (
            ('view_keyword__dep', 'View Keyword Deprecated'),
        )

    def __str__(self):
        return "{}".format(self.name)

class KeywordMeta(models.Model):
    keyword = models.ForeignKey(Keyword, related_name="keyword_metas", on_delete=models.CASCADE, db_index=True)
    organization = models.ForeignKey(Organization, related_name="organization_keyword_metas",
                                     on_delete=models.SET_NULL, null=True, db_index=True)
    planning_months = models.ManyToManyField(
        PlanningYearMonth, related_name="planning_year_month_keyword_metas", blank=True, db_index=True)
    tag = models.ManyToManyField(ContentTag, related_name="tag_keyword_metas", blank=True)
    seo_value = models.CharField(choices=VALUE_OPTIONS, max_length=100, default="Low", null=True, blank=True)
    business_value = models.CharField(choices=VALUE_OPTIONS, max_length=100, default="Low", null=True, blank=True)
    active = models.BooleanField(default=True, blank=True)
    created_by = models.ForeignKey(User, related_name="created_keyword_metas", null=True, on_delete=models.SET_NULL)
    date_created = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Keyword Meta"
        verbose_name_plural = "Keywords Metas"
        permissions = (
            ('view_keywordmeta__dep', 'View Keyword Meta Deprecated'),
        )

    def __str__(self):
        return "{}".format(self.id)

class UrlRanking(models.Model):
    url = models.URLField(max_length=500)
    keyword = models.ForeignKey(Keyword, related_name="url_rankings", on_delete=models.CASCADE)
    ahrefs_rank = models.PositiveSmallIntegerField(default=1)
    ahrefs_locations = models.CharField(max_length=255, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "URL Ranking"
        verbose_name_plural = "URL Rankings"
        permissions = (
            ('view_urlranking__dep', 'View URL Ranking Deprecated'),
        )

    def __str__(self):
        return "{} - {}".format(self.url, self.keyword.name)

class Writer(models.Model):
    user = models.OneToOneField(User, related_name="writer", on_delete=models.CASCADE, db_index=True)
    rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    rating = models.PositiveSmallIntegerField(null=True, default=0.00)

    class Meta:
        verbose_name = "Writer"
        verbose_name_plural = "Writers"
        permissions = (
            ('view_writer__dep', 'View Writer Deprecated'),
        )

    def __str__(self):
        return "{}".format(self.id)

class ContentArticleQuerySet(models.QuerySet):

    def as_of(self, date):
        history_objects = list()
        for article in self:
            article_as_of = article.get_history_as_of(date)
            if article_as_of:
                history_objects.append(article_as_of)
        queryset = list(chain(history_objects))

        return queryset


class ContentArticle(models.Model):
    planning_year_month = models.ForeignKey(PlanningYearMonth, null=True, related_name="contentArticle", on_delete=models.SET_NULL, db_index=True)
    project = models.ForeignKey(ContentProject, null=True, blank=True, related_name="project_articles", on_delete=models.SET_NULL, db_index=True)
    title = models.CharField(max_length=255, db_index=True)
    google_doc = models.URLField(max_length=500, blank=True, null=True)
    admin_draft_url = models.URLField(max_length=500, blank=True, null=True)
    live_url = models.URLField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    content_type = models.ForeignKey(ContentType, related_name="contentType", on_delete=models.SET_NULL, null=True)
    channels = models.ManyToManyField(ContentChannel, blank=True)
    keywords = models.ManyToManyField(KeywordMeta, blank=True, related_name="keyword_meta_articles")
    focus_keyword_plaintext = models.CharField(max_length=255, blank=True, null=True)
    status = models.ForeignKey(ContentStatus, null=True, related_name="contentStatus",
                               on_delete=models.SET_NULL, db_index=True)
    client = models.ForeignKey(Organization, related_name="contentClient",
                               on_delete=models.SET_NULL, null=True, db_index=True)
    writer = models.ForeignKey(Writer, related_name="contentWriter",
                               on_delete=models.SET_NULL, blank=True, null=True, db_index=True)
    editor = models.ForeignKey(User, related_name="contentEditor", on_delete=models.SET_NULL,
                               blank=True, null=True, db_index=True)
    poster = models.ForeignKey(User, related_name="contentPoster", on_delete=models.SET_NULL,
                               blank=True, null=True, db_index=True)
    final_approver = models.ForeignKey(User, related_name="contentApprover",
                                       on_delete=models.SET_NULL, blank=True, null=True, db_index=True)
    lead = models.ForeignKey(User, related_name="contentLead",
                                       on_delete=models.SET_NULL, blank=True, null=True, db_index=True)
    min_word_count = models.PositiveSmallIntegerField(blank=True, null=True)
    milestone = models.CharField(blank=True, null=True, choices=MILESTONES, max_length=25)
    duedate_write = models.DateField(blank=True, null=True, db_index=True)
    duedate_rewrite = models.DateField(blank=True, null=True)
    duedate_edit = models.DateField(blank=True, null=True)
    duedate_reedit = models.DateField(blank=True, null=True)
    duedate_finalreview = models.DateField(blank=True, null=True)
    duedate_schedulepost = models.DateTimeField(blank=True, null=True)
    duedate_qapost = models.DateField(blank=True, null=True)
    duedate_golive = models.DateField(blank=True, null=True)
    price_production = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    price_distribution = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    url_1 = models.URLField(null=True, blank=True)
    anchor_1 = models.CharField(max_length=255, null=True, blank=True)
    url_2 = models.URLField(null=True, blank=True)
    anchor_2 = models.CharField(max_length=255, null=True, blank=True)
    scheduled_date = models.DateField(blank=True, null=True)
    writer_planned_duedate = models.DateField(blank=True, null=True)
    archived = models.BooleanField(blank=True, default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    objects = ContentArticleQuerySet.as_manager()

    def get_api_view_name(self):
        api_view_name = 'content_articles'
        return api_view_name

    def get_history_as_of(self, date):
        history = self.history
        try:
            if history and history.all().first():
                history_as_of = history.as_of(date)
                return history_as_of
            else:
                return None
        except:
            return None

    @property
    def is_late(self):
        today_datetime = timezone.now()
        today_date = today_datetime.date()
        status = self.status
        # status_due_date_offset = status.due_date_day_offset

        if self.duedate_schedulepost:
            duedate_schedulepost = datetime.datetime.combine(self.duedate_schedulepost, datetime.time(17,0))
            duedate_schedulepost = timezone.make_aware(duedate_schedulepost)
        else:
            duedate_schedulepost = None

        if status:
            if status.uid == 'writing':
                if self.duedate_write:
                    if self.duedate_write < today_date:
                        return True
                    else:
                        return False
                else:
                    return None

            elif status.uid == 'rewrite':
                if self.duedate_rewrite:
                    if self.duedate_rewrite < today_date:
                        return True
                    else:
                        return False
                else:
                    return None

            elif status.uid == 'editing':
                if self.duedate_edit:
                    if self.duedate_edit < today_date:
                        return True
                    else:
                        return False
                else:
                    return None

            elif status.uid == 'reedit':
                if self.duedate_reedit:
                    if self.duedate_reedit < today_date:
                        return True
                    else:
                        return False
                else:
                    return None
            
            elif status.uid == 'final_review':
                if self.duedate_finalreview:

                # Only count it if we are the final approver
                    # should_count = False
                    # if self.final_approver:
                    #     if self.final_approver.is_staff:
                    #         should_count = True

                    # if self.duedate_finalreview < today_date and should_count:
                    if self.duedate_finalreview < today_date:
                        return True
                    else:
                        return False
                else:
                    return None
            
            elif status.uid == 'ready_to_post':
                if self.duedate_schedulepost and duedate_schedulepost:
                    if duedate_schedulepost < today_datetime:
                        return True
                    else:
                        return False
                else:
                    return None

            elif status.uid == 'post_qa':
                if self.duedate_qapost:
                    if self.duedate_qapost < today_date:
                        return True
                    else:
                        return False
                else:
                    return None

            elif status.uid == 'scheduled' or status.uid == 'posted':
                if self.duedate_golive:
                    if self.duedate_golive < today_date:
                        return True
                    else:
                        return False
                else:
                    return None

            else:
                return None
        else:
            return None

    class Meta:
        verbose_name = "Content Article"
        verbose_name_plural = "Content Articles"
        permissions = (
            ('view_contentarticle__dep', 'View Content Article Deprecated'),
            ('create_google_doc', 'Create Google Doc'),
            ('edit_contentarticle', 'Edit Content Article'),
            ('write_contentarticle', 'Write Content Article'),
            ('approve_contentarticle', 'Approver Content Article'),
        )
        ordering = ['status__order', 'planning_year_month__year', 'planning_year_month__month']

    # @transaction.atomic
    # def save(self, *args, **kwargs):
    #     if getattr(self, 'status', None) is None:
    #         self.status = self.planning_year_month.default_status
    #     super(ContentArticle, self).save(*args, **kwargs)

    def __str__(self):
        return "{}".format(self.title)

class ContentArticleHistorySet(models.Model):
    as_of_date = models.DateTimeField(null=True, blank=True)
    year = models.IntegerField(validators=[MinValueValidator(2017), MaxValueValidator(2050)], null=True, blank=True)
    month = models.PositiveSmallIntegerField(choices=MONTHS.items(), null=True, blank=True)
    day = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(31)], null=True, blank=True)
    status = models.ForeignKey(ContentStatus, related_name="corresponding_article_history_set", on_delete=models.CASCADE)
    incomplete_count = models.PositiveSmallIntegerField(blank=True, null=True)
    complete_count = models.PositiveSmallIntegerField(blank=True, null=True)
    late_count = models.PositiveSmallIntegerField(blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def populate_set(self, fromHistory=False, delay=True):
        if delay:
            populate_article_history_set.delay(self.id, fromHistory)
            print('running populate_set with delay')
        else:
            populate_article_history_set(self.id, fromHistory)
            print('running populate_set WITHOUT delay')

    @transaction.atomic
    def save(self, *args, **kwargs):
        now = timezone.now()
        aod = getattr(self, 'as_of_date', None)
        if getattr(self, 'as_of_date', None) is None:
            print('in save function, no as_of_date found')
            if self.year and self.month and self.day:
                new_as_of_date = datetime.datetime(self.year, self.month, self.day)
            else:
                new_as_of_date = now
            self.as_of_date = new_as_of_date
        else:
            print(f'in save function, as_of_date found. It is {aod}')
            if not self.year or not self.month or not self.day:
                self.year = self.as_of_date.year
                self.month = self.as_of_date.month
                self.day = self.as_of_date.day
        super(ContentArticleHistorySet, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Content Article History Set"
        verbose_name_plural = "Content Article History Sets"
        unique_together = ("status", "year", "month", "day",)
        ordering = ['-as_of_date']

    def __str__(self):
        return f'Article History set as of {self.as_of_date.strftime("%m-%d-%Y")}'

class ContentComments(models.Model):
    article = models.ForeignKey(ContentArticle, related_name="contentComments", on_delete=models.CASCADE)
    author =  models.ForeignKey(User, related_name="contentCommentAuthor", on_delete=models.CASCADE)
    comment = models.TextField()
    public = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Content Comment"
        verbose_name_plural = "Content Comments"
        permissions = (
            ('view_contentcomments__dep', 'View Content Comments Deprecated'),
        )

    def __str__(self):
        return "{}: {}".format(self.author, self.article)

class PlanningTemplateOrder(models.Model):
    article_order_array = ArrayField(models.IntegerField(), default=list, null=True, blank=True)

    class Meta:
        verbose_name = "Planning Template"
        verbose_name_plural = "Planning Templates"
        permissions = (
            ('view_planningtemplateorder__dep', 'View Planning Template Order Deprecated'),
        )

    def __str__(self):
        return self.article_order_array

class ArticleTemplate(models.Model):
    title = models.CharField(max_length=200, db_index=True)
    content_type = models.ForeignKey(ContentType, related_name="defaultContentType", on_delete=models.SET_NULL, null=True,)
    content_channels = models.ManyToManyField(ContentChannel, blank=True)
    client = models.ForeignKey(Organization, related_name="defaultOrganizationTemplate", on_delete=models.SET_NULL, null=True)
    writer = models.ForeignKey(Writer, related_name="defaultWriter", on_delete=models.SET_NULL, null=True)
    editor = models.ForeignKey(User, related_name="defaultEditor", on_delete=models.SET_NULL, null=True, blank=True)
    lead = models.ForeignKey(User, related_name="defaultLead", on_delete=models.SET_NULL, null=True, blank=True)
    poster = models.ForeignKey(User, related_name="defaultPoster", on_delete=models.SET_NULL, null=True, blank=True)
    final_approver = models.ForeignKey(User, related_name="defaultApprover", on_delete=models.SET_NULL, null=True, blank=True)
    min_word_count = models.PositiveSmallIntegerField(null=True)
    milestone = models.CharField(blank=True, null=True, choices=MILESTONES, max_length=25)
    price_production = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    price_distribution = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    production_notes = models.TextField(null=True)
    archived = models.BooleanField(blank=True, default=False)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    last_update = models.DateTimeField(auto_now=True, null=True)
    history = HistoricalRecords()

    def get_api_view_name(self):
        api_view_name = 'article_templates'
        return api_view_name
    
    class Meta:
        verbose_name = "Default Content Template"
        verbose_name_plural = "Default Content Templates"
        permissions = (
            ('view_articletemplate__dep', 'View Article Template Deprecated'),
        )
        ordering = ['client__dba_name', 'title']
    
    def __str__(self):
        return "{}".format(self.title)

class OrganizationEditorialRequirement(models.Model):
    organization = models.ForeignKey(Organization, related_name="editorial_requirements", on_delete=models.CASCADE)
    requirement = models.CharField(max_length=255)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    last_update = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name = "Organization Editorial Requirement"
        verbose_name_plural = "Organization Editorial Requirements"
        permissions = (
            ('view_organizationeditorialrequirement__dep', 'Organization Editorial Requirement Deprecated'),
        )
    
    def __str__(self):
        return "{}: {}".format(self.id, self.organization.id)


class OrganizationRequirements(models.Model):
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name="organization_requirements")
    blog_count = models.PositiveSmallIntegerField(null=True, blank=True)
    press_release_count = models.PositiveSmallIntegerField(null=True, blank=True)
    blog_word_count = models.PositiveSmallIntegerField(null=True, blank=True)
    needs_approval = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Organization Requirement"
        verbose_name_plural = "Organization Requirements"
        permissions = (
            ('view_organizationrequirements__dep', 'View Organization Requirements Deprecated'),
        )

    def __str__(self):
        return "{}'s contract requirements".format(self.organization.dba_name)


class Feedback(models.Model):
    article = models.ForeignKey(ContentArticle, related_name="article_feedback", on_delete=models.CASCADE)
    satisfaction = models.PositiveSmallIntegerField(null=True, default=0, blank=True)
    feedback_body = models.TextField()
    given_by = models.ForeignKey(User, related_name="user_feedback", on_delete=models.CASCADE, null=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    approved = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Feedback"
        verbose_name_plural = "Feedback"
        permissions = (
            ('view_feedback__dep', 'View Feedback Deprecated'),
        )

    def __str__(self):
        return "{}: {} - Approved: {}".format(self.article.id, self.given_by.name, self.approved)


class ContentRequirement(models.Model):
    organization = models.ForeignKey(Organization, related_name="org_content_requirements", on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, related_name="related_requirements", on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(default=1)
    year = models.IntegerField(validators=[MinValueValidator(2017), MaxValueValidator(2050)], default=current_year())
    month = models.PositiveSmallIntegerField(choices=MONTHS.items(), default=current_month())
    month_count = models.SmallIntegerField(default=-1)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    last_updated = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name = "Content Requirement"
        verbose_name_plural = "Content Requirements"
        permissions = (
            ('view_contentrequirement__dep', 'View Content Requirement Deprecated'),
        )

    def __str__(self):
        return "{}: {} {}".format(self.organization.dba_name, self.quantity, self.content_type.name)