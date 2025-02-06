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
            "id": self.id,
            "title": self.title,
            "artist": self.artist,
            "size": self.size,
            "duration": self.duration,
            "album": self.album,
            "genre": self.genre if self.genre else "No genre",
            "image": self.image.url if self.image else None,
        }

    def __str__(self) -> str:
        return {
            "title": self.title,
            "artist": self.artist,
            "duration": self.duration,
            "size": self.size,
            "album": self.album,
            "genre": self.genre if self.genre else "No genre",
            "image": self.image.url if self.image else None,
        }.__str__()

    def __repr__(self) -> str:
        return self.__str__()

    def key(self) -> str:
        return SongKey(self.title, self.artist)


class SongKey:

    def __init__(self, title: str, artist: str):
        self.title: str = title
        self.artist: str = artist

    @staticmethod
    def from_string(key: str) -> "SongKey":
        title, artist = key.split("-")
        return SongKey(title, artist)

    def __str__(self) -> str:
        return f"{self.title}-{self.artist}"

    def key(self) -> tuple[str, str]:
        return self.title, self.artist
