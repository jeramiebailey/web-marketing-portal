from rest_framework import serializers
from .models import UserFeedback

class UserFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFeedback
        fields = ('__all__')