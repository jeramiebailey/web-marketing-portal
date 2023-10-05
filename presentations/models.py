from django.db import models, transaction
from django.db.models import F, Max
from docker_drf_backend.users.models import User
import uuid
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from datetime import datetime  
from datetime import timedelta

class SlideManager(models.Manager):

    def move(self, obj, new_order):

        qs = self.get_queryset()

        with transaction.atomic():
            if obj.order > int(new_order):
                qs.filter(
                    slide_deck=obj.slide_deck,
                    order__lt=obj.order,
                    order__gte=new_order,
                ).exclude(
                    pk=obj.pk
                ).update(
                    order=F('order') + 1,
                )
            else:
                qs.filter(
                    slide_deck=obj.slide_deck,
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
            slides = self.filter(
                    slide_deck=instance.slide_deck
                )

            results = slides.aggregate(
                    Max('order')
                )

            if instance.order:
                slides.filter(
                    order__gte=instance.order,
                ).update(
                    order=F('order') + 1,
                )
        
            else:
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
            
class SlideDeck(models.Model):
    name = models.CharField(max_length=200)
    content_type = models.ForeignKey(ContentType, blank=True, null=True, on_delete=models.SET_NULL, related_name="slide_decks")
    object_id = models.PositiveIntegerField(blank=True, null=True)
    object_instance = GenericForeignKey('content_type', 'object_id')
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    last_updated = models.DateTimeField(auto_now=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    archived = models.BooleanField(blank=True, default=False)

    def get_api_view_name(self):
        api_view_name = 'slide_decks'
        return api_view_name

    class Meta:
        verbose_name = "Slide Deck"
        verbose_name_plural = "Slide Decks"
        permissions = (
            ('view_slidedeck__dep', 'View Slide Deck Deprecated'),
        )

    def __str__(self):
        return "{}".format(self.name)


class Slide(models.Model):
    slide_deck = models.ForeignKey(SlideDeck, related_name="slides", on_delete=models.SET_NULL, blank=True, null=True)
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    components = JSONField(null=True, blank=True)
    content_type = models.ForeignKey(ContentType, blank=True, null=True, on_delete=models.SET_NULL, related_name="slide_deck_slides")
    object_id = models.PositiveIntegerField(blank=True, null=True)
    object_instance = GenericForeignKey('content_type', 'object_id')
    order = models.IntegerField(default=0, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    last_updated = models.DateTimeField(auto_now=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    active = models.BooleanField(blank=True, default=True)

    objects = SlideManager()

    def get_api_view_name(self):
        api_view_name = 'slides'
        return api_view_name

    class Meta:
        verbose_name = "Slide"
        verbose_name_plural = "Slides"
        permissions = (
            ('view_slide__dep', 'View Slide Deprecated'),
        )
        index_together = ('slide_deck', 'order')
        ordering = ['slide_deck', 'order']
    
    def __str__(self):
        return "{}: {}".format(self.slide_deck, self.title)


class SlideDeckTemplate(models.Model):
    name = models.CharField(max_length=200)
    use_dynamic_title = models.BooleanField(blank=True, default=True)
    content_type = models.ForeignKey(ContentType, blank=True, null=True, on_delete=models.SET_NULL, related_name="slide_deck_templates")
    object_id = models.PositiveIntegerField(blank=True, null=True)
    object_instance = GenericForeignKey('content_type', 'object_id')
    is_master_template = models.BooleanField(blank=True, default=False)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    last_updated = models.DateTimeField(auto_now=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    archived = models.BooleanField(blank=True, default=False)

    class Meta:
        verbose_name = "Slide Deck Template"
        verbose_name_plural = "Slide Deck Templates"
        permissions = (
            ('view_slidedecktemplate__dep', 'View Slide Deck Template Deprecated'),
        )
        unique_together = (("content_type", "is_master_template"))

    def cascade_from_master_template(self, object_id, name=None, derived_fields=None):
        if self.is_master_template and self.content_type:
            template_content_type = self.content_type
            if name:
                new_template_name = name
            else:
                new_template_name = self.name

            created_template = SlideDeckTemplate.objects.create(
                name=new_template_name,
                object_id=object_id,
            )

            corrresponding_slide_templates = self.slide_templates.all()
            
            for slide in corrresponding_slide_templates:

                created_slide_template = SlideTemplate.objects.create(
                    slide_deck=created_template,
                    title = slide.title,
                    content = slide.content,
                    components = slide.components,
                    content_type = slide.content_type,
                    object_id = slide.object_id,
                    order = slide.order,
                )

                if derived_fields:
                    updated_components = created_slide_template.components
                    for derived_field in derived_fields:
                        for component in updated_components:
                            for field in component['fields']:
                                if field['name'] == derived_field:
                                    field['data'] = object_id
                
                created_slide_template.components = updated_components
                created_slide_template.save()

            created_template.save()

            return created_template

    
    def create_slide_deck(
            self, 
            name=None, 
            slide_deck_object_type=None, 
            slide_deck_object_id=None,
            slide_object_type=None,
            slide_object_id=None,
        ):


        if name:
            new_name = name
        else:
            new_name = 'New {}'.format(self.name)
        try:
            slides = SlideTemplate.objects.filter(slide_deck=self)
        except:
            slides = None

        if slide_deck_object_type:
            new_object_type = slide_deck_object_type
        else:
            new_object_type = self.content_type

        if slide_deck_object_id:
            new_object_id = slide_deck_object_id
        else:
            new_object_id = self.object_id
            
        new_slide_deck = SlideDeck.objects.create(
            name=new_name,
            content_type=new_object_type,
            object_id=new_object_id,
        )
        new_slide_deck.save()

        if slides:
            for slide in slides:
                if slide_object_type:
                    content_type = slide_object_type
                else:
                    content_type = slide.content_type

                if slide_object_id:
                    object_id = slide_object_id
                else:
                    object_id = slide.object_id

                new_slide = Slide.objects.create(
                    slide_deck=new_slide_deck,
                    content_type=content_type,
                    object_id=object_id,
                    title=slide.title,
                    order=slide.order,
                    components=slide.components,
                    content=slide.content,
                )
                new_slide.save()
        
        return new_slide_deck
    
    def __str__(self):
        return "{}".format(self.name)


class SlideTemplate(models.Model):
    slide_deck = models.ForeignKey(SlideDeckTemplate, related_name="slide_templates", on_delete=models.SET_NULL, blank=True, null=True)
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    components = JSONField(null=True, blank=True)
    content_type = models.ForeignKey(ContentType, blank=True, null=True, on_delete=models.SET_NULL, related_name="slide_deck_template_slides")
    object_id = models.PositiveIntegerField(blank=True, null=True)
    object_instance = GenericForeignKey('content_type', 'object_id')
    order = models.IntegerField(default=0, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    last_updated = models.DateTimeField(auto_now=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    active = models.BooleanField(blank=True, default=True)

    objects = SlideManager()

    class Meta:
        verbose_name = "Slide Template"
        verbose_name_plural = "Slide Templates"
        permissions = (
            ('view_slidetemplate__dep', 'View Slide Template Deprecated'),
        )
        index_together = ('slide_deck', 'order')
        ordering = ['slide_deck', 'order']
    
    def __str__(self):
        return "{}: {}".format(self.slide_deck.name, self.title)