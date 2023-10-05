from django.db import models
from simple_history.models import HistoricalRecords
from django.db import models, transaction
from django.db.models import F, Max
from docker_drf_backend.users.models import User
from .constants import DEPARTMENTS
import uuid
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from datetime import datetime  
from datetime import timedelta

class ItemManager(models.Manager):

    def move(self, obj, new_order):

        qs = self.get_queryset()

        with transaction.atomic():
            if obj.order > int(new_order):
                qs.filter(
                    checklist=obj.checklist,
                    order__lt=obj.order,
                    order__gte=new_order,
                ).exclude(
                    pk=obj.pk
                ).update(
                    order=F('order') + 1,
                )
            else:
                qs.filter(
                    checklist=obj.checklist,
                    order__lte=new_order,
                    order__gt=obj.order,
                ).exclude(
                    pk=obj.pk,
                ).update(
                    order=F('order') - 1,
                )

            obj.order = new_order
            obj.save()
    
    def create(self, **kwargs):
        instance = self.model(**kwargs)

        with transaction.atomic():
            checklist_items = self.filter(
                    checklist=instance.checklist
                )

            results = checklist_items.aggregate(
                    Max('order')
                )

            if instance.order:
                checklist_items.filter(
                    order__gte=instance.order,
                ).update(
                    order=F('order') + 1,
                )
        
            else:
                # Increment and use it for our new object
                try:
                    current_order = results['order__max'] + 1

                except: 
                    current_order = None


                if current_order is None:
                    current_order = 0

                value = current_order
                instance.order = value
            instance.save()

            return instance

class Checklist(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    archived = models.BooleanField(blank=True, default=False)
    created_by = models.ForeignKey(User, related_name="user_checklist", null=True, on_delete=models.SET_NULL)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    last_updated = models.DateTimeField(auto_now=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Checklist"
        verbose_name_plural = "Checklists"
        permissions = (
            ('view_checklist__dep', 'View Checklist Deprecated'),
        )

    def __str__(self):
        return "{}".format(self.name)

class ChecklistItem(models.Model):
    checklist = models.ForeignKey(Checklist, related_name="checklist_items", on_delete=models.CASCADE)
    parent = models.ForeignKey("self", related_name="checklist_item_children", null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=200)
    order = models.IntegerField(default=0, blank=True, null=True)
    description = models.TextField(blank=True)
    department = models.CharField(max_length=255, choices=DEPARTMENTS, null=True, blank=True)
    assignee = models.ForeignKey(User, related_name="checklist_item_assignments", null=True, blank=True, on_delete=models.SET_NULL)
    due = models.DateField(blank=True, null=True)
    completed = models.BooleanField(blank=True, default=False)
    created_by = models.ForeignKey(User, related_name="user_checklist_items", null=True, on_delete=models.SET_NULL)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    last_updated = models.DateTimeField(auto_now=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    history = HistoricalRecords()

    objects = ItemManager()

    class Meta:
        verbose_name = "Checklist Item"
        verbose_name_plural = "Checklist Items"
        permissions = (
            ('view_checklistitem__dep', 'View Checklist Item Deprecated'),
        )
        index_together = ('checklist', 'order')
        ordering = ['checklist', 'order']
    
    def __str__(self):
        return "{}: {}".format(self.checklist.name, self.name)

class ChecklistTemplate(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    archived = models.BooleanField(blank=True, default=False)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(User, related_name="user_checklist_templates", null=True, on_delete=models.SET_NULL)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    last_updated = models.DateTimeField(auto_now=True, null=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Checklist Template"
        verbose_name_plural = "Checklist Templates"
        permissions = (
            ('view_checklisttemplate__dep', 'View Checklist Template Deprecated'),
        )
    
    def create_checklist(self, user, name=None, start_date=None):
        if name:
            new_name = name
        else:
            new_name = 'New {}'.format(self.name)
        if user:
            created_by = user
        else:
            user = None
        try:
            items = ChecklistTemplateItem.objects.filter(checklist=self)
        except:
            items = None
        new_checklist = Checklist.objects.create(
            name=new_name,
            created_by=created_by,
        )
        new_checklist.save()
        has_parent = items.filter(parent__isnull=False)
        no_parent = items.filter(parent=None)
        for item in no_parent:
            if start_date and item.days_out:
                due = start_date + timedelta(days=item.days_out)
            else:
                due = None
            new_checklist_item = ChecklistItem.objects.create(
                checklist=new_checklist,
                name=item.name,
                order=item.order,
                description=item.description,
                department=item.department,
                due=due,
                assignee=item.default_assignee,
                created_by=created_by,
            )
            new_checklist_item.save()
            attachments = item.checklist_template_item_attachments
            if attachments is not None:
                for attachment in attachments.all():
                    new_attachment = ChecklistItemAttachment.objects.create(
                        upload=attachment.upload,
                        description=attachment.description,
                        checklist_item=new_checklist_item,
                        uploaded_by=created_by,
                    )
                    new_attachment.save()
        for item in has_parent:
            try:
                parent = ChecklistItem.objects.get(checklist=new_checklist, name=item.parent.name)
            except:
                parent = None

            if start_date and item.days_out:
                due = start_date + timedelta(days=item.days_out)
            else:
                due = None
            new_checklist_item = ChecklistItem.objects.create(
                checklist=new_checklist,
                parent=parent,
                name=item.name,
                order=item.order,
                due=due,
                description=item.description,
                department=item.department,
                assignee=item.default_assignee,
                created_by=created_by,
            )
            new_checklist_item.save()
            attachments = item.checklist_template_item_attachments
            if attachments is not None:
                for attachment in attachments.all():
                    new_attachment = ChecklistItemAttachment.objects.create(
                        upload=attachment.upload,
                        description=attachment.description,
                        checklist_template_item=new_checklist_item,
                        uploaded_by=created_by,
                    )
                    new_attachment.save()
        
        return new_checklist
    
    def __str__(self):
        return "{}".format(self.name)

class ChecklistTemplateItem(models.Model):
    checklist = models.ForeignKey(ChecklistTemplate, related_name="template_items", on_delete=models.CASCADE)
    parent = models.ForeignKey("self", related_name="checklist_template_item_children", null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=200, blank=True, default="")
    order = models.IntegerField(default=0, blank=True, null=True)
    description = models.TextField(blank=True)
    department = models.CharField(max_length=255, choices=DEPARTMENTS, null=True, blank=True)
    days_out = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(365)])
    default_assignee = models.ForeignKey(User, related_name="checklist_template_item_assignments", null=True, blank=True, on_delete=models.SET_NULL)
    created_by = models.ForeignKey(User, related_name="user_checklist_template_items", null=True, on_delete=models.SET_NULL)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    last_updated = models.DateTimeField(auto_now=True, null=True)
    history = HistoricalRecords()

    objects = ItemManager()

    class Meta:
        verbose_name = "Checklist Template Item"
        verbose_name_plural = "Checklist Template Items"
        permissions = (
            ('view_checklisttemplateitem__dep', 'View Checklist Template Item Deprecated'),
        )
        index_together = ('checklist', 'order')
        ordering = ['checklist', 'order']
    
    def __str__(self):
        return "{}: {}".format(self.checklist.name, self.name)

class ChecklistTemplateItemAttachment(models.Model):
    upload = models.FileField(upload_to='uploads/checklist_item_attachments/')
    description = models.TextField(blank=True)
    checklist_template_item = models.ForeignKey(ChecklistTemplateItem, related_name="checklist_template_item_attachments", null=True, blank=True, on_delete=models.SET_NULL)
    uploaded_by = models.ForeignKey(User, related_name="user_checklist_template_item_uploads", null=True, on_delete=models.SET_NULL)
    date_uploaded = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        verbose_name = "Checklist Template Item Attachment"
        verbose_name_plural = "Checklist Template Item Attachments"
        permissions = (
            ('view_checklisttemplateitemattachment__dep', 'View Checklist Template Item Attachment Deprecated'),
        )
    
    def __str__(self):
        return "{}: {}".format(self.checklist_template_item.name, self.date_uploaded)

class ChecklistItemAttachment(models.Model):
    upload = models.FileField(upload_to='uploads/checklist_item_attachments/')
    description = models.TextField(blank=True)
    checklist_item = models.ForeignKey(ChecklistItem, related_name="checklist_item_attachments", null=True, blank=True, on_delete=models.SET_NULL)
    uploaded_by = models.ForeignKey(User, related_name="user_checklist_item_uploads", null=True, on_delete=models.SET_NULL)
    date_uploaded = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        verbose_name = "Checklist Item Attachment"
        verbose_name_plural = "Checklist Item Attachments"
        permissions = (
            ('view_checklistitemattachment__dep', 'View Checklist Item Attachment Deprecated'),
        )
    
    def __str__(self):
        return "{}: {}".format(self.checklist_item.name, self.date_uploaded)


class MasterChecklistTemplate(models.Model):
    website_build = models.ForeignKey(ChecklistTemplate, related_name="website_build_master", on_delete=models.SET_NULL, null=True, blank=True)
    website_deployment = models.ForeignKey(ChecklistTemplate, related_name="website_deployment_master", on_delete=models.SET_NULL, null=True, blank=True)
    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        if MasterChecklistTemplate.objects.exists() and not self.pk:
            raise ValidationError('There is can be only one Master Checklist Template Reference')
        return super(MasterChecklistTemplate, self).save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Master Checklist Templates"
        verbose_name_plural = "Master Checklist Templates"
        permissions = (
            ('view_masterchecklisttemplate__dep', 'View Master Checklist Templates Deprecated'),
        )