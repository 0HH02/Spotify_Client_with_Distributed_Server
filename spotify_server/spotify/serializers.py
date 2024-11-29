from rest_framework import serializers
from .models import Song


class SongMetadataSerializer(serializers.Serializer):
    class Meta:
        model = Song
        fields: list[str] = [
            "id",
            "title",
            "artist",
            "album",
            "genre",
            "image",
        ]


class ClientUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def validate_file(self, value):

        if not value.name.endswith(".mp3"):
            raise serializers.ValidationError("Only .mp3 files are allowed.")

        return value


class SongSerializer(serializers.Serializer):
    class Meta:
        model = Song
        fields: list[str] = [
            "id",
            "title",
            "artist",
            "album",
            "genre",
            "image",
            "audio",
        ]
