from rest_framework.response import Response
from rest_framework import mixins, status, viewsets, permissions
from .models import SlideDeckTemplate, SlideDeck, Slide, SlideTemplate
from .serializers import SlideDeckTemplateSerializer, SlideDeckSerializer, SlideSerializer, SlideTemplateSerializer
from guardian.shortcuts import assign_perm, remove_perm
from api.permissions import CustomObjectPermissions
from rest_framework_guardian import filters
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action

class SlideDeckTemplateViewSet(viewsets.ModelViewSet):
    queryset = SlideDeckTemplate.objects.prefetch_related(
        'slide_templates', 
        ).all()
    serializer_class = SlideDeckTemplateSerializer
    permission_classes = (IsAuthenticated,)

class SlideTemplateViewSet(viewsets.ModelViewSet):
    queryset = SlideTemplate.objects.select_related('slide_deck').all()
    serializer_class = SlideTemplateSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = self.queryset
        slide_deck_template_query = self.request.query_params.get('slideDeckTemplate', None)

        if slide_deck_template_query:
            try:
                slide_deck_template = SlideDeckTemplate.objects.get(id=slide_deck_template_query)
            except:
                slide_deck_template = None
            if slide_deck_template:
                queryset = queryset.filter(slide_deck=slide_deck_template)
                return queryset
        
        return queryset

    def perform_create(self, serializer):
        slide_template = serializer.save()
        return slide_template

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_slide = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        updatedSlides = SlideTemplate.objects.select_related('slide_deck').filter(slide_deck=new_slide.slide_deck)
        output_serializer = SlideTemplateSerializer(updatedSlides, many=True, context={'request': request})
        data = output_serializer.data
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        updatedSlides = SlideTemplate.objects.select_related('slide_deck').filter(slide_deck=instance.slide_deck)
        output_serializer = SlideTemplateSerializer(updatedSlides, many=True, context={'request': request})
        data = output_serializer.data
        return Response(data)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        updatedSlides = SlideTemplate.objects.select_related('slide_deck').filter(slide_deck=instance.slide_deck)
        output_serializer = SlideTemplateSerializer(updatedSlides, many=True, context={'request': request})
        data = output_serializer.data
        return Response(data, status=status.HTTP_202_ACCEPTED)

    @action(methods=['post'], detail=True)
    def move(self, request, pk):
        obj = self.get_object()
        new_order = request.data.get('order', None)

        if new_order is None:
            return Response(
                data={'error': 'No order given'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if int(new_order) < 0:
            return Response(
                data={'error': 'Order cannot be less than zero'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        SlideTemplate.objects.move(obj, new_order)
        updatedSlideTemplates = SlideTemplate.objects.select_related('slide_deck').filter(slide_deck=obj.slide_deck)
        serializer = SlideTemplateSerializer(updatedSlideTemplates, many=True, context={'request': request})
        data = serializer.data
        return Response(data)

class SlideDeckViewSet(viewsets.ModelViewSet):
    queryset = SlideDeck.objects.prefetch_related(
        'slides', 
        ).all()
    serializer_class = SlideDeckSerializer
    permission_classes = (IsAuthenticated,)


class SlideViewSet(viewsets.ModelViewSet):
    queryset = Slide.objects.select_related('slide_deck').all()
    serializer_class = SlideSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = self.queryset
        slide_deck_query = self.request.query_params.get('slideDeckTemplate', None)

        if slide_deck_query:
            try:
                slide_deck = SlideDeck.objects.get(id=slide_deck_query)
            except:
                slide_deck = None
            if slide_deck:
                queryset = queryset.filter(slide_deck=slide_deck)
                return queryset
        
        return queryset
    
    def perform_create(self, serializer):
        slide = serializer.save()
        return slide

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_slide = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        updatedSlides = Slide.objects.select_related('slide_deck').filter(slide_deck=new_slide.slide_deck)
        output_serializer = SlideSerializer(updatedSlides, many=True, context={'request': request})
        data = output_serializer.data
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        updatedSlides = Slide.objects.select_related('slide_deck').filter(slide_deck=instance.slide_deck)
        output_serializer = SlideSerializer(updatedSlides, many=True, context={'request': request})
        data = output_serializer.data
        return Response(data)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        updatedSlides = Slide.objects.select_related('slide_deck').filter(slide_deck=instance.slide_deck)
        output_serializer = SlideSerializer(updatedSlides, many=True, context={'request': request})
        data = output_serializer.data
        return Response(data, status=status.HTTP_202_ACCEPTED)

    @action(methods=['post'], detail=True)
    def move(self, request, pk):
        obj = self.get_object()
        new_order = request.data.get('order', None)

        if new_order is None:
            return Response(
                data={'error': 'No order given'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if int(new_order) < 0:
            return Response(
                data={'error': 'Order cannot be less than zero'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        Slide.objects.move(obj, new_order)
        updatedSlides = Slide.objects.select_related('slide_deck').filter(slide_deck=obj.slide_deck)
        serializer = SlideSerializer(updatedSlides, many=True, context={'request': request})
        data = serializer.data
        return Response(data)