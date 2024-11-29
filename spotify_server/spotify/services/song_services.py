"""
This module contains the services for the Song model.
"""

import io
from typing import IO
from django.core.files import File
from django.db.models.manager import BaseManager
from django.db import models


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
    def upload_song(file: IO) -> SongMetadataSerializer:
        """"""
        file_bytes: bytes = file.read()
        song: DecodedSong = Mp3Decoder.decode(file_bytes)
        image: File | None = (
            File(
                io.BytesIO(song.image.image_data),
                name=file.name + "img" + song.image.file_extension,
            )
            if song.image is not None
            else None
        )

        created_song: Song = Song(
            title=song.title,
            artist=song.artist,
            album=song.album,
            genre=song.genre,
            image=image,
            audio=File(io.BytesIO(song.audio_data), name=file.name),
        )

        created_song.save()

        return SongMetadataSerializer(created_song)
