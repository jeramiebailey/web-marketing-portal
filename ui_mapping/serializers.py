from rest_framework import serializers
from .models import UIComponent

class UIComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UIComponent
        fields = ('__all__')