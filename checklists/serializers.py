from rest_framework import serializers
from docker_drf_backend.users.serializers import BriefUserDetailsSerializer
from .models import ChecklistTemplate, ChecklistTemplateItem, Checklist, ChecklistItem, ChecklistTemplateItemAttachment, ChecklistItemAttachment, MasterChecklistTemplate

class ChecklistTemplateItemAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistTemplateItemAttachment
        fields = ('__all__')
        
class ChecklistItemAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItemAttachment
        fields = ('__all__')

# class ChecklistTemplateItemListSerializer(serializers.ListSerializer):

#     class Meta:
#         fields = ('__all__')

#     def update(self, instance, validated_data):
#         template_item_mapping = {template_item.id: template_item for template_item in instance}

#         data_mapping = {item['id']: item for item in validated_data}

#         template_items = []
#         for template_item_id, data in data_mapping.items():
  
#             template_item = template_item_mapping.get(template_item_id, None)
#             if template_item is None:
#                 template_items.append(self.child.create(data))
#             else:
#                 template_items.append(self.child.update(template_item, data))

#         for template_item_id, template_item in template_item_mapping.items():
#             if template_item_id not in data_mapping:
#                 template_item.delete()

#         return template_items

class ChecklistTemplateItemSerializer(serializers.ModelSerializer):
    checklist_template_item_attachments = ChecklistTemplateItemAttachmentSerializer(many=True, read_only=True)
    checklist_template_item_children = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    
    def to_representation(self, instance):
        response = super().to_representation(instance)
        if instance.default_assignee:
            if self.context:
                response['default_assignee'] = BriefUserDetailsSerializer(instance.default_assignee,  context={'request': self.context['request']}).data
            else:
                response['default_assignee'] = BriefUserDetailsSerializer(instance.default_assignee).data
        return response

    class Meta:
        model = ChecklistTemplateItem
        #list_serializer_class = ChecklistTemplateItemListSerializer
        fields = ('__all__')

class ChecklistTemplateSerializer(serializers.ModelSerializer):
    template_items = ChecklistTemplateItemSerializer(read_only=True, many=True)

    class Meta:
        model = ChecklistTemplate
        fields = ('__all__')


class ChecklistItemSerializer(serializers.ModelSerializer):
    checklist_item_attachments = ChecklistItemAttachmentSerializer(many=True, read_only=True)
    checklist_item_children = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    def to_representation(self, instance):
        response = super().to_representation(instance)
        if instance.assignee:
            if self.context:
                response['assignee'] = BriefUserDetailsSerializer(instance.assignee,  context={'request': self.context['request']}).data
            else:
                response['assignee'] = BriefUserDetailsSerializer(instance.assignee).data
        return response

    class Meta:
        model = ChecklistItem
        fields = ('__all__')

class ChecklistSerializer(serializers.ModelSerializer):
    checklist_items = ChecklistItemSerializer(read_only=True, many=True)

    class Meta:
        model = Checklist
        fields = ('__all__')

class MasterChecklistTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MasterChecklistTemplate
        fields = ('__all__')