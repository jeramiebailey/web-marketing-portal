from rest_framework import serializers
from .models import ChildTheme, WebApp

class WebAppSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebApp
        fields = ('__all__')

class ChildThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChildTheme
        fields = ('__all__')

class ChildThemeForeignKey(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return ChildTheme.objects.filter(available=True)

class InitializeWPBuildSerializer(serializers.Serializer):
    website_build = serializers.IntegerField(min_value=1, allow_null=True, required=False)
    child_theme = ChildThemeForeignKey()
    # repo_name = serializers.CharField(max_length=255, allow_blank=True)
    # site_url = serializers.URLField(max_length=250, allow_blank=True)
    
class ConfirmCompleteWPBuildSerializer(serializers.Serializer):
    application_uuid = serializers.UUIDField()
    secret_key = serializers.CharField(max_length=255, allow_blank=False)

class GenerateS3DownloadSerializer(serializers.Serializer):
    file_key = serializers.CharField(max_length=999, allow_blank=False)