from rest_framework import serializers
from account_health.models import AccountHealth
from organizations.serializers import OrganizationSerializer
from api.serializers import ContentArticleSerializer
import json

class AccountHealthSerializer(serializers.ModelSerializer):
    account = OrganizationSerializer(many=False, read_only=True)

    def to_representation(self, instance):
        response = super(AccountHealthSerializer, self).to_representation(instance)
        overdue_approvals = json.dumps(instance.get_overdue_approvals(as_list=True))
        response['overdue_approvals'] = json.loads(overdue_approvals)

        return response

    class Meta:
        model = AccountHealth
        fields = ('__all__')