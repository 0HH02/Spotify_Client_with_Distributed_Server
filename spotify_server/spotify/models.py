from django.db import models

# pylint: disable=no-member


class Song(models.Model):
    title = models.CharField(max_length=255)
    artist = models.CharField(max_length=255)
    album = models.CharField(max_length=255, null=True)
    genre = models.CharField(max_length=255, null=True)
    image = models.FileField(upload_to="song_images/", null=True)
    audio = models.FileField(upload_to="songs/")

    def to_dict_metadata(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "genre": self.genre if self.genre else "No genre",
            "image": self.image.url if self.image else None,
        }

    def __str__(self) -> str:
        return {
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "genre": self.genre if self.genre else "No genre",
            "image": self.image.url if self.image else None,
        }.__str__()

    def __repr__(self) -> str:
        return self.__str__()
