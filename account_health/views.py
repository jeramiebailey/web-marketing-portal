from rest_framework.response import Response
from rest_framework import mixins, status, viewsets
from account_health.models import AccountHealth
from account_health.serializers import AccountHealthSerializer
from rest_framework_guardian import filters
from api.permissions import CustomObjectPermissions
from content_management.serializers import BriefContentArticleSerializer
from rest_framework.decorators import action

class AccountHealthViewSet(viewsets.ModelViewSet):
    queryset = AccountHealth.objects.select_related('account').prefetch_related('account__what_converts_account').filter(account__is_active=True).order_by('account__dba_name')
    serializer_class = AccountHealthSerializer
    permission_classes = (CustomObjectPermissions,)
    filter_backends = (filters.DjangoObjectPermissionsFilter,)

    @action(detail=True, methods=['get'])
    def get_overdue_approvals(self, request, pk=None):
        instance = self.get_object()
        overdue_approvals = instance.get_overdue_approvals()
        response = BriefContentArticleSerializer(overdue_approvals, many=True)

        return Response(response.data, status=status.HTTP_200_OK)