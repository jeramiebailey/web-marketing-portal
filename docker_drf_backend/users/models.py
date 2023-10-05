from django.contrib.auth.models import AbstractUser, Group
from django.db.models import CharField
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.db import models
from simple_history.models import HistoricalRecords
from django.apps import apps
from django.db.models import Q
from datetime import timedelta, datetime, time
from django.utils import timezone

class User(AbstractUser):
    name = CharField(_("Name of User"), blank=True, max_length=255)
    title = models.CharField(blank=True, max_length=255, null=True)
    phone_number = models.CharField(max_length=17, null=True, blank=True)
    avatar = models.ImageField(upload_to="uploads/user_avatars/", null=True, blank=True)
    default_role = models.ForeignKey(Group, related_name="user_default_role",
                                     on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    history = HistoricalRecords() 

    class Meta:
        permissions = (
            ('view_user__dep', 'View User Deprecated'),
        )

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})

    def get_all_content_assignments(self):
        ContentArticle = apps.get_model(app_label='content_management', model_name='ContentArticle')
        ContentStatus = apps.get_model(app_label='content_management', model_name='ContentStatus')
        applicable_statuses = ContentStatus.objects.filter(status_type="Active")

        queryset = ContentArticle.objects.select_related( 
            'writer',
            'client',
            'poster',
            'lead',
            'editor',
            'planning_year_month',
            'project',
            'content_type',
            'status',
            'final_approver').prefetch_related(
                'content_type',
                'contentComments',
                'writer__user',
                'keywords',
                'channels',
            ).filter(
            Q(editor=self) |
            Q(writer__user=self) |
            Q(poster=self) |
            Q(final_approver=self) |
            Q(lead=self),
            Q(planning_year_month__isnull=False) |
            Q(project__isnull=False),
            status__in=applicable_statuses,
            writer__isnull=False,
            archived=False
        ).distinct().order_by('status__order', 'planning_year_month__year', 'planning_year_month__month', 'milestone')

        return queryset

    def get_all_late_assignments(self):
        all_assignments = self.get_all_content_assignments()
        all_late_assignment_ids = [obj.id for obj in all_assignments if obj.is_late]
        all_late_assignments = all_assignments.filter(id__in=all_late_assignment_ids)

        return all_late_assignments

    def get_due_soon_assignments(self, days_out=3):
        all_assignments = self.get_all_content_assignments()
        today_datetime = timezone.now()
        today_date = today_datetime.date()
        target_date = today_date + timedelta(days=days_out)
        target_date_time = today_datetime + timedelta(days=days_out)

        writing_due_soon_ids = [obj.id for obj in all_assignments if obj.status.uid == 'writing' and obj.duedate_write and obj.duedate_write < target_date and obj.duedate_write > today_date and obj.writer and obj.writer.user.id == self.id]
        rewrite_due_soon_ids = [obj.id for obj in all_assignments if obj.status.uid == 'rewrite' and obj.duedate_rewrite and obj.duedate_rewrite < target_date and obj.duedate_rewrite > today_date and obj.writer and obj.writer.user.id == self.id]
        editing_due_soon_ids = [obj.id for obj in all_assignments if obj.status.uid == 'editing' and obj.duedate_edit and obj.duedate_edit < target_date and obj.duedate_edit > today_date and obj.editor and obj.editor.id == self.id]
        reedit_due_soon_ids = [obj.id for obj in all_assignments if obj.status.uid == 'reedit' and obj.duedate_reedit and obj.duedate_reedit < target_date and obj.duedate_reedit > today_date and obj.editor and obj.editor.id == self.id]
        final_review_due_soon_ids = [obj.id for obj in all_assignments if obj.status.uid == 'final_review' and obj.duedate_finalreview and obj.duedate_finalreview < target_date and obj.duedate_finalreview > today_date and obj.final_approver and obj.final_approver.id == self.id]
        posting_due_soon_ids = [obj.id for obj in all_assignments if obj.status.uid == 'ready_to_post' and obj.duedate_schedulepost and obj.duedate_schedulepost < target_date_time and obj.duedate_schedulepost > today_datetime and obj.poster and obj.poster.id == self.id]
        post_qa_due_soon_ids = [obj.id for obj in all_assignments if obj.status.uid == 'post_qa' and obj.duedate_qapost and obj.duedate_qapost < target_date and obj.duedate_qapost > today_date and obj.lead and obj.lead.id == self.id]

        all_due_soon_ids = [
            *writing_due_soon_ids,
            *rewrite_due_soon_ids,
            *editing_due_soon_ids,
            *reedit_due_soon_ids,
            *final_review_due_soon_ids,
            *posting_due_soon_ids,
            *post_qa_due_soon_ids,
        ]

        all_due_soon_assignments = all_assignments.filter(id__in=all_due_soon_ids)

        return all_due_soon_assignments



class Preferences(models.Model):
    user = models.OneToOneField(User, related_name="user_preferences",
                                on_delete=models.CASCADE, primary_key=True, db_index=True)
    avatar_color = models.CharField(max_length=10, blank=True, default='#888888')
    nick_name = models.CharField(max_length=255, blank=True, null=True)
    default_organization = models.ForeignKey(
            'organizations.Organization', 
            related_name="user_default_organization", 
            on_delete=models.CASCADE, 
            null=True, 
            blank=True, 
            db_index=True
        )
    
    class Meta:
        verbose_name = "User Preferences"
        verbose_name_plural = "User Preferences"
        permissions = (
            ('view_preferences__dep', 'View Preferences Deprecated'),
        )

    def __str__(self):
        return "{} preferences".format(self.user.username)

class UserOrgRole(models.Model):
    user = models.ForeignKey(User, related_name="org_roles", on_delete=models.CASCADE, db_index=True)
    organization = models.ForeignKey('organizations.Organization',
                                     related_name="user_roles", on_delete=models.CASCADE, db_index=True)
    role = models.ForeignKey(Group, related_name="user_org_roles", on_delete=models.CASCADE, db_index=True)
    receive_reporting_email = models.NullBooleanField(blank=True, default=False)
    receive_approval_reminders = models.NullBooleanField(blank=True, default=False)
    history = HistoricalRecords() 

    class Meta:
        ordering = ('organization',)
        verbose_name = "User Organization Role"
        verbose_name_plural = "User Organization Roles"
        unique_together = (("user", "organization", "role"))
        permissions = (
            ('view_userorgrole__dep', 'View User Org Role Deprecated'),
        )

    def __str__(self):
        return "{} - {} : {}".format(self.user.name, self.organization.dba_name, self.role.name)
