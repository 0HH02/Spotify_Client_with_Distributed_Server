# music/serializers.py

from rest_framework import serializers


class MusicSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField(max_length=255)
    gender = serializers.ListField(child=serializers.CharField(max_length=100))
    artist = serializers.ListField(child=serializers.CharField(max_length=255))
    album = serializers.CharField(max_length=255)
    root = serializers.CharField(max_length=500)
    imageUrl = serializers.CharField(max_length=500)
