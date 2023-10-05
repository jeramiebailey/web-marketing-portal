from rest_framework import serializers

class CheckBrokenLinksSerializer(serializers.Serializer):
    url = serializers.URLField(max_length=250, min_length=None, allow_blank=False)