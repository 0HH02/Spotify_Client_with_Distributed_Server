"""
This module contains the services for the Song model.
"""

import io
from django.core.files import File
from django.db.models.manager import BaseManager
from django.db import models
from django.conf import settings
from rest_framework.serializers import FileField


from .mp3_decoder import Mp3Decoder, DecodedSong
from ..models import Song
from ..serializers import SongMetadataSerializer

# pylint: disable=no-member


class SongServices:
    """"""

    @staticmethod
    def get_all_songs_metadata() -> BaseManager[Song]:
        """ """
        return Song.objects.all()

    @staticmethod
    def search_songs(search_by, query) -> BaseManager[Song]:

        if search_by == "artist":
            return Song.objects.filter(artist__icontains=query)
        if search_by == "genre":
            return Song.objects.filter(genre__icontains=query)
        if search_by == "title":
            return Song.objects.filter(title__icontains=query)

        return Song.objects.filter(
            models.Q(title__icontains=query)
            | models.Q(artist__icontains=query)
            | models.Q(album__icontains=query)
            | models.Q(genre__icontains=query)
        )

    @staticmethod
    def upload_song(file: FileField) -> Song:
        """"""
        file_bytes: bytes = file.read()
        song: DecodedSong = Mp3Decoder.decode(file_bytes)
        image: File | None = (
            File(
                io.BytesIO(song.image.image_data),
                name=file.name + "img" + song.image.file_extension,
            )
            if song.image
            else None
        )

        created_song: Song = Song(
            title=song.title,
            artist=song.artist,
            album=song.album,
            genre=song.genre,
            image=image,
            audio=file,
        )

        created_song.save()

        return created_song

    @staticmethod
    def stream_song(song_id: int, range: tuple[int, int] = None):
        """"""
        try:
            song: Song = Song.objects.get(id=song_id)

            audio_file: models.FieldFile = song.audio.open("rb")
            file_size: int = audio_file.size

            start, end = range if range else (0, file_size - 1)
            end = min(end, file_size - 1)

            length: int = end - start + 1

            audio_file.seek(start)

            def file_iterator(
                file: models.FieldFile,
                length: int,
                chunk_size=settings.STREAM_CHUNK_SIZE,
            ):
                bytes_remaining = length
                while bytes_remaining > 0:
                    read_size = min(chunk_size, bytes_remaining)
                    data: bytes = file.read(read_size)
                    if not data:
                        break
                    yield data
                    bytes_remaining -= len(data)

            return file_iterator(audio_file, length)

        except Song.DoesNotExist:
            return None
