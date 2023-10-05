from rest_framework import serializers
from .models import SlideDeckTemplate, SlideDeck, Slide, SlideTemplate
from api.serializers import DynamicHyperlinkedRelatedField
from organizations.models import Organization

class SlideTemplateSerializer(serializers.ModelSerializer):
    object_instance = DynamicHyperlinkedRelatedField(
        many=False,
        read_only=True,
        view_name=''
    )

    class Meta:
        model = SlideTemplate
        fields = ('__all__')
        extra_kwargs = {'id': {'read_only': False, 'required': False}}

class SlideDeckTemplateSerializer(serializers.ModelSerializer):
    slide_templates = SlideTemplateSerializer(many=True)
    object_instance = DynamicHyperlinkedRelatedField(
        many=False,
        read_only=True,
        view_name=''
    )

    def create(self, validated_data):
        slide_templates = validated_data.pop('slide_templates')
        instance = super(SlideDeckTemplateSerializer, self).create(validated_data)
        if (slide_templates is not None):
            for template in slide_templates:
                new_slide = SlideTemplate.objects.create(slide_deck=instance, **template)
                new_slide.save()
        instance.save()
        try:
            organization = Organization.objects.get(id=instance.object_id)
        except:
            organization = None
        if organization:
            organization.monthly_report_template = instance
            organization.save()

        return instance

    def update(self, instance, validated_data):
        slide_templates = validated_data.pop('slide_templates')
        slide_template_serializer = SlideTemplateSerializer()
        super(SlideDeckTemplateSerializer, self).update(instance, validated_data)

        if (slide_templates is not None):
            old_slide_templates = instance.slide_templates
            new_slide_template_ids = []

            for template in slide_templates:
                template_id = template.get('id', None)

                if template_id:
                    try:
                        existing_slide_template = SlideTemplate.objects.get(id=template_id)
                    except:
                        existing_slide_template = None
                
                    if existing_slide_template:
                        new_slide_template_ids.append(existing_slide_template.id)
                        super(SlideTemplateSerializer, slide_template_serializer).update(existing_slide_template, template)

                else:
                    new_slide = super(SlideTemplateSerializer, slide_template_serializer).create(template)
                    new_slide.slide_deck = instance
                    new_slide.save()
                    new_slide_template_ids.append(new_slide.id)

            if new_slide_template_ids and new_slide_template_ids[0]:
                old_templates = old_slide_templates.exclude(pk__in=new_slide_template_ids)
                if old_templates:
                    old_templates.delete()
                
        instance.save()

        return instance
    
    class Meta:
        model = SlideDeckTemplate
        fields = ('__all__')


class SlideSerializer(serializers.ModelSerializer):
    object_instance = DynamicHyperlinkedRelatedField(
        many=False,
        read_only=True,
        view_name=''
    )

    class Meta:
        model = Slide
        fields = ('__all__')


class SlideDeckSerializer(serializers.ModelSerializer):
    slides = SlideSerializer(many=True)
    object_instance = DynamicHyperlinkedRelatedField(
        many=False,
        read_only=True,
        view_name=''
    )

    class Meta:
        model = SlideDeck
        fields = ('__all__')