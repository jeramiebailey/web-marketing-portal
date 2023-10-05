from rest_framework import serializers
from .models import WebsiteBuild
from django.db import transaction
from checklists.models import MasterChecklistTemplate
from api.serializers import OrganizationSerializer
from wp_deployments.serializers import WebAppSerializer

class WebsiteBuildSerializer(serializers.ModelSerializer):
    new_application = WebAppSerializer(many=False, read_only=True)

    class Meta:
        model = WebsiteBuild
        fields = ('__all__')
    
    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['organization'] = OrganizationSerializer(instance.organization).data
        return response

    @transaction.atomic
    def create(self, validated_data):
        user = self.context['request'].user
        build_name = validated_data.get('label')
        start_date = validated_data.get('start_date')

        try:
            master_checklist_template = MasterChecklistTemplate.objects.all().first()
        except:
            master_checklist_template = None

        if master_checklist_template:
            try:
                master_build_checklist = master_checklist_template.website_build
            except:
                master_build_checklist = None
            try:
                master_deploy_checklist = master_checklist_template.website_deployment
            except:
                master_deploy_checklist = None

            if master_build_checklist:
                new_build_checklist = master_build_checklist.create_checklist(
                    user=user, 
                    name="{}: {}".format(master_build_checklist.name, build_name),
                    start_date=start_date
                )
            else:
                new_build_checklist = None
            if master_deploy_checklist:
                new_deployment_checklist = master_deploy_checklist.create_checklist(
                    user=user, 
                    name="{}: {}".format(master_deploy_checklist.name, build_name),
                    start_date=start_date
                )
            else:
                new_deployment_checklist = None

        return WebsiteBuild.objects.create(
            build_checklist=new_build_checklist,
            deploy_checklist=new_deployment_checklist,
            **validated_data
        )

    