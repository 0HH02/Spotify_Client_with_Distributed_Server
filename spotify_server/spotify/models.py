from django.db import models

# pylint: disable=no-member


class Song(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    artist = models.CharField(max_length=255, db_index=True)
    duration = models.FloatField(default=0.0)
    size = models.IntegerField(default=0)
    album = models.CharField(max_length=255, null=True)
    genre = models.CharField(max_length=255, null=True)
    image = models.FileField(upload_to="song_images/", null=True)
    audio = models.FileField(upload_to="songs/")

    def to_dict_metadata(self) -> dict:
        return {
            "title": self.title,
            "artist": self.artist,
            "size": self.size,
            "duration": self.duration,
            "album": self.album,
            "genre": self.genre if self.genre else "unknown",
            "image": self.image.url if self.image else None,
        }

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "artist": self.artist,
            "size": self.size,
            "duration": self.duration,
            "album": self.album,
            "genre": self.genre if self.genre else "unknown",
            "image": {
                "image_data": self.image.read(),
                "file_extension": self.image.name.split(".")[-1],
            },
            "audio_data": self.audio.read(),
        }

    def __str__(self) -> str:
        return {
            "title": self.title,
            "artist": self.artist,
            "duration": self.duration,
            "size": self.size,
            "album": self.album,
            "genre": self.genre if self.genre else "unknown",
            "image": self.image.url if self.image else None,
        }.__str__()

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def key(self):
        return f"{self.title}-{self.artist}"
