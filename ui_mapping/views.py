from rest_framework.response import Response
from rest_framework import mixins, status, viewsets, permissions
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import UIComponent
from .serializers import UIComponentSerializer

class UIComponentViewSet(viewsets.ModelViewSet):
    queryset = UIComponent.objects.filter(is_allowed=True)
    serializer_class = UIComponentSerializer
    permission_classes = (IsAuthenticated,)
