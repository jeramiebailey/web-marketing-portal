from rest_framework import serializers
from .models import Organization, WhatConvertsAccount
import json

class WhatConvertsAccountSerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        response = super(WhatConvertsAccountSerializer, self).to_representation(instance)
        try:
            organization = Organization.objects.get(what_converts_account=instance)
        except:
            organization = None

        if organization:
            response['organization'] = organization.id

        return response

    class Meta:
        model = WhatConvertsAccount
        fields = ('__all__')

class OrganizationSerializer(serializers.ModelSerializer):
    what_converts_account = WhatConvertsAccountSerializer(many=False, read_only=False, required=False, allow_null=True)
    class Meta:
        model = Organization
        fields = (
            'id',
            'legal_name',
            'dba_name',
            'slug',
            'business_email',
            'phone_number',
            'street_address_1',
            'street_address_2',
            'city',
            'state',
            'zipcode',
            'domain',
            'logo',
            'google_analytics_id',
            'what_converts_account',
            'is_active',
            'report_required',
            'monthly_report_template',
            'contract_start_date',
            'account_lead',
            'project_manager',
            'created_at',
            'updated_at',
        )

    # def create(self, validated_data):
    #     what_converts_account = validated_data.pop('what_converts_account')
    #     print('serializer what_converts_account is: ', what_converts_account)
    #     instance = super(OrganizationSerializer, self).create(validated_data)
    #     what_converts_account_serializer = WhatConvertsAccountSerializer()
    #     if (what_converts_account is not None):
    #         new_what_converts_account = super(WhatConvertsAccountSerializer, what_converts_account_serializer).create(what_converts_account)
    #         instance.what_converts_account = new_what_converts_account
    #     instance.save()

    #     return instance

    def create(self, validated_data):
        try:
            what_converts_account = validated_data.pop('what_converts_account')
            what_converts_account = json.loads(what_converts_account)
        except:
            what_converts_account = None
        instance = super(OrganizationSerializer, self).create(validated_data)
        what_converts_account_serializer = WhatConvertsAccountSerializer()
        if (what_converts_account is not None):
            new_what_converts_account = super(WhatConvertsAccountSerializer, what_converts_account_serializer).create(what_converts_account)
            instance.what_converts_account = new_what_converts_account
        instance.save()

        return instance

    # def update(self, instance, validated_data):
    #     what_converts_account = validated_data.pop('what_converts_account')
    #     print('serializer what_converts_account is: ', what_converts_account)
    #     what_converts_account_serializer = WhatConvertsAccountSerializer()
    #     instance = super(OrganizationSerializer, self).update(instance, validated_data)

    #     if instance.what_converts_account and (what_converts_account is not None):
    #         updated_what_converts_account = super(WhatConvertsAccountSerializer, what_converts_account_serializer).update(instance.what_converts_account, what_converts_account)
            
    #     elif not instance.what_converts_account and (what_converts_account is not None):
    #         new_what_converts_account = super(WhatConvertsAccountSerializer, what_converts_account_serializer).create(what_converts_account)
    #         instance.what_converts_account = new_what_converts_account
                
    #     instance.save()

    #     return instance

    
    def update(self, instance, validated_data):
        try:
            what_converts_account = validated_data.pop('what_converts_account')
            what_converts_account = json.loads(what_converts_account)
        except:
            what_converts_account = None
        what_converts_account_serializer = WhatConvertsAccountSerializer()
        instance = super(OrganizationSerializer, self).update(instance, validated_data)

        if instance.what_converts_account and (what_converts_account is not None):
            updated_what_converts_account = super(WhatConvertsAccountSerializer, what_converts_account_serializer).update(instance.what_converts_account, what_converts_account)
            
        elif not instance.what_converts_account and (what_converts_account is not None):
            new_what_converts_account = super(WhatConvertsAccountSerializer, what_converts_account_serializer).create(what_converts_account)
            instance.what_converts_account = new_what_converts_account
                
        instance.save()

        return instance


class DetailedOrganizationSerializer(OrganizationSerializer):
    what_converts_account = WhatConvertsAccountSerializer(many=False, read_only=False, required=False, allow_null=True)
    class Meta:
        model = Organization
        fields = (
            '__all__'
        )