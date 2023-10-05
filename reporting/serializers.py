from rest_framework import serializers
from .models import MonthlyReport, ReportEmailEntry
from organizations.models import Organization
from content_management.models import PlanningYearMonth

class ReportEmailEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportEmailEntry
        fields = ('__all__')

class MonthlyReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyReport
        fields = ('__all__')
        read_only_fields = [
            'referring_domains_screenshot',
            'referring_pages_screenshot',
            'organic_keywords_screenshot',
            'detailed_organic_keywords_screenshot'
        ]


class PlanningMonthForeignKey(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return PlanningYearMonth.objects.all()

class OrganizationForeignKey(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return Organization.objects.filter(is_active=True, report_required=True)

class MonthlyReportActionsSerializer(serializers.Serializer):
    planning_month = PlanningMonthForeignKey()

class MonthlyReportTemplateSerializer(serializers.Serializer):
    organizations = serializers.ListField(child=OrganizationForeignKey())