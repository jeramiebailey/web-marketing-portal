from rest_framework.response import Response
from rest_framework import mixins, status, viewsets, permissions
from .models import ChecklistTemplate, ChecklistTemplateItem, Checklist, ChecklistItem, ChecklistTemplateItemAttachment, ChecklistItemAttachment, MasterChecklistTemplate
from .serializers import ChecklistTemplateSerializer, ChecklistTemplateItemSerializer, ChecklistSerializer, ChecklistItemSerializer, ChecklistTemplateItemAttachmentSerializer, ChecklistItemAttachmentSerializer, MasterChecklistTemplateSerializer
from guardian.shortcuts import assign_perm, remove_perm
from api.permissions import CustomObjectPermissions
from rest_framework_guardian import filters
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.decorators import (api_view, detail_route, list_route,
                                       permission_classes)

#anchor
class ChecklistTemplateViewSet(viewsets.ModelViewSet):
    queryset = ChecklistTemplate.objects.select_related('created_by').prefetch_related(
        'template_items', 
        'template_items__checklist', 
        'template_items__checklist_template_item_children',
        'template_items__parent', 
        'template_items__checklist_template_item_attachments'
        ).all()
    serializer_class = ChecklistTemplateSerializer
    permission_classes = (IsAuthenticated,)
    # filter_backends = (filters.DjangoObjectPermissionsFilter,)

    def perform_create(self, serializer):
        checklist_template = serializer.save(created_by=self.request.user)
        assign_perm('view_checklisttemplate', self.request.user, checklist_template)
        checklist_template.save()
    

class ChecklistTemplateItemViewSet(viewsets.ModelViewSet):
    queryset = ChecklistTemplateItem.objects.select_related('parent', 'default_assignee', 'checklist').prefetch_related(
        'parent__checklist',
        'checklist__template_items',
        'checklist__template_items__checklist',
        'checklist_template_item_children',
        'checklist_template_item_attachments', 
        'default_assignee__user_preferences', 
        'default_assignee__user_preferences__default_organization',
        ).all()
    serializer_class = ChecklistTemplateItemSerializer
    permission_classes = (IsAuthenticated,)
    # filter_backends = (filters.DjangoObjectPermissionsFilter,)

    # def get_serializer(self, *args, **kwargs):
    #     if "data" in kwargs:
    #         data = kwargs["data"]

    #         if isinstance(data, list):
    #             many = True
    #             data_ids = []
    #             for obj in data:
    #                 data_ids.append(obj['id'])
    #             checklist_template_items = self.queryset.filter(id__in=data_ids)
                
    #             serializer = ChecklistTemplateItemSerializer(instance=checklist_template_items, data=data, many=many)
    #             return serializer     
    #         else:
    #             return super(ChecklistTemplateItemViewSet, self).get_serializer(*args, **kwargs)
    #     else:
    #         return super(ChecklistTemplateItemViewSet, self).get_serializer(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_item = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        updatedChecklistItems = ChecklistTemplateItem.objects.select_related('parent', 'default_assignee').filter(checklist=new_item.checklist)
        output_serializer = ChecklistTemplateItemSerializer(updatedChecklistItems, many=True)
        data = output_serializer.data
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        updatedChecklistItems = ChecklistTemplateItem.objects.select_related('parent', 'default_assignee').filter(checklist=instance.checklist)
        output_serializer = ChecklistTemplateItemSerializer(updatedChecklistItems, many=True)
        data = output_serializer.data
        return Response(data)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        updatedChecklistItems = ChecklistTemplateItem.objects.select_related('parent', 'default_assignee').filter(checklist=instance.checklist)
        output_serializer = ChecklistTemplateItemSerializer(updatedChecklistItems, many=True)
        data = output_serializer.data
        return Response(data, status=status.HTTP_202_ACCEPTED)

    def perform_create(self, serializer):
        checklist_template_item = serializer.save(created_by=self.request.user)
        assign_perm('view_checklisttemplateitem', self.request.user, checklist_template_item)
        return checklist_template_item

    @action(methods=['post'], detail=True)
    def move(self, request, pk):
        obj = self.get_object()
        new_order = request.data.get('order', None)

        # Make sure we received an order 
        if new_order is None:
            return Response(
                data={'error': 'No order given'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Make sure our new order is not below one
        if int(new_order) < 0:
            return Response(
                data={'error': 'Order cannot be less than zero'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ChecklistTemplateItem.objects.move(obj, new_order)
        updatedChecklistTemplateItems = ChecklistTemplateItem.objects.select_related('parent', 'default_assignee').filter(checklist=obj.checklist)
        serializer = ChecklistTemplateItemSerializer(updatedChecklistTemplateItems, many=True)
        data = serializer.data
        return Response(data)
    
class ChecklistViewSet(viewsets.ModelViewSet):
    queryset = Checklist.objects.select_related('created_by').prefetch_related(
        'checklist_items',
        'checklist_items__assignee',
        'checklist_items__checklist_item_children',
        'checklist_items__checklist_item_attachments',
        ).all()
    serializer_class = ChecklistSerializer
    permission_classes = (IsAuthenticated,)
    # filter_backends = (filters.DjangoObjectPermissionsFilter,)

    def perform_create(self, serializer):
        checklist = serializer.save(created_by=self.request.user)
        assign_perm('view_checklist', self.request.user, checklist)
        checklist.save()
    

class ChecklistItemViewSet(viewsets.ModelViewSet):
    queryset = ChecklistItem.objects.select_related('parent', 'assignee', 'checklist').prefetch_related(
        'checklist_item_children',
        'checklist_item_attachments', 
        'assignee__user_preferences', 
        'assignee__user_preferences__default_organization'
        ).all()
    serializer_class = ChecklistItemSerializer
    permission_classes = (IsAuthenticated,)
    # filter_backends = (filters.DjangoObjectPermissionsFilter,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_item = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        updatedChecklistItems = ChecklistItem.objects.select_related('parent', 'assignee').filter(checklist=new_item.checklist)
        output_serializer = ChecklistItemSerializer(updatedChecklistItems, many=True)
        data = output_serializer.data
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        updatedChecklistItems = ChecklistItem.objects.select_related('parent', 'assignee').filter(checklist=instance.checklist)
        output_serializer = ChecklistItemSerializer(updatedChecklistItems, many=True)
        data = output_serializer.data
        return Response(data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        updatedChecklistItems = ChecklistItem.objects.select_related('parent', 'assignee').filter(checklist=instance.checklist)
        output_serializer = ChecklistItemSerializer(updatedChecklistItems, many=True)
        data = output_serializer.data
        return Response(data, status=status.HTTP_202_ACCEPTED)

    def perform_create(self, serializer):
        checklist_item = serializer.save(created_by=self.request.user)
        assign_perm('view_checklistitem', self.request.user, checklist_item)
        return checklist_item
    
class ChecklistTemplateItemAttachmentViewSet(viewsets.ModelViewSet):
    queryset = ChecklistTemplateItemAttachment.objects.select_related('checklist_template_item').prefetch_related('checklist_template_item__checklist').all()
    serializer_class = ChecklistTemplateItemAttachmentSerializer
    permission_classes = (IsAuthenticated,)
    # filter_backends = (filters.DjangoObjectPermissionsFilter,)

    def perform_create(self, serializer):
        checklist_template_item_attachment = serializer.save(uploaded_by=self.request.user)
        assign_perm('view_checklisttemplateitemattachment', self.request.user, checklist_template_item_attachment)
        checklist_template_item_attachment.save()

class ChecklistItemAttachmentViewSet(viewsets.ModelViewSet):
    queryset = ChecklistItemAttachment.objects.select_related('checklist_item').prefetch_related('checklist_item__checklist').all()
    serializer_class = ChecklistItemAttachmentSerializer
    permission_classes = (IsAuthenticated,)
    # filter_backends = (filters.DjangoObjectPermissionsFilter,)

    def perform_create(self, serializer):
        checklist_item_attachment = serializer.save(uploaded_by=self.request.user)
        assign_perm('view_checklistitemattachment', self.request.user, checklist_item_attachment)
        checklist_item_attachment.save()

# class MasterChecklistTemplateViewSet(viewsets.ModelViewSet):
#     queryset = MasterChecklistTemplate.objects.all()
#     serializer_class = MasterChecklistTemplateSerializer
#     permission_classes = (IsAuthenticated,)

# @api_view(('POST', 'GET'))
# @permission_classes((AllowAny,))
# def get_master_checklist_templates(request):
#     master_templates = MasterChecklistTemplate.objects.all().first()
#     serializer = MasterChecklistTemplateSerializer(master_templates, many=False)
#     return Response(serializer.data, status=status.HTTP_200_OK)

class MasterChecklistTemplateViewSet(viewsets.ModelViewSet):
    queryset = MasterChecklistTemplate.objects.all()
    serializer_class = MasterChecklistTemplateSerializer
    permission_classes = (IsAuthenticated,)