from rest_framework.response import Response
from rest_framework import mixins, status, viewsets, permissions
from .models import WebsiteBuild
from .serializers import WebsiteBuildSerializer
from guardian.shortcuts import assign_perm, remove_perm
from api.permissions import CustomObjectPermissions
from rest_framework_guardian import filters
from rest_framework.permissions import AllowAny, IsAuthenticated
from checklists.models import MasterChecklistTemplate

class WebsiteBuildViewSet(viewsets.ModelViewSet):
    queryset = WebsiteBuild.objects.select_related('organization', 'build_checklist', 'deploy_checklist').filter(is_active=True).order_by('-date_created')
    serializer_class = WebsiteBuildSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.DjangoObjectPermissionsFilter,)

    def get_queryset(self):
        queryset = WebsiteBuild.objects.select_related('organization', 'build_checklist', 'deploy_checklist').filter(is_active=True).order_by('-date_created')
        archived = self.request.query_params.get('archived', None)

        if archived:
            queryset = WebsiteBuild.objects.select_related('organization', 'build_checklist', 'deploy_checklist').filter(is_active=False).order_by('-date_created')

        return queryset