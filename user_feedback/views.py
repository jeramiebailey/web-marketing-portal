from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import mixins, status, viewsets, permissions
from .models import UserFeedback
from .serializers import UserFeedbackSerializer
from guardian.shortcuts import assign_perm, remove_perm
from api.permissions import CustomObjectPermissions
from rest_framework_guardian import filters
from rest_framework.permissions import AllowAny, IsAuthenticated

class UserFeedbackViewSet(viewsets.ModelViewSet):
    queryset = UserFeedback.objects.all()
    serializer_class = UserFeedbackSerializer
    permission_classes = (IsAuthenticated,)
    # filter_backends = (filters.DjangoObjectPermissionsFilter,)

    def perform_create(self, serializer):
        user_feedback = serializer.save(user=self.request.user)
        assign_perm('view_userfeedback', self.request.user, user_feedback)
        user_feedback.save()
