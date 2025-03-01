"""
This module contains the services for the Song model.
"""

import io
from django.core.files import File
from django.db.models.manager import BaseManager
from django.db import models
from django.db.models.fields.files import FieldFile
from django.conf import settings


from ..models import Song
from ..distributed_layer.song_dto import SongKey, SongDto
from ..logs import write_log

# pylint: disable=no-member


class SongServices:
    """"""

    @staticmethod
    def get_song(song_key: SongKey) -> Song | None:
        title, artist = song_key.key
        return Song.objects.filter(title=title, artist=artist).first()

    @staticmethod
    def exists_song(song_key: SongKey) -> bool:
        """"""
        title, artist = song_key.key
        return Song.objects.filter(title=title, artist=artist).exists()

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
    def upload_song(song: SongDto) -> Song:
        """"""
        try:
            image: File | None = (
                File(
                    io.BytesIO(song.image.image_data),
                    name=str(song.key) + "img." + song.image.file_extension,
                )
                if song.image
                else None
            )
            audio: File = File(io.BytesIO(song.audio_data), name=str(song.key) + ".mp3")

            created_song: Song = Song(
                title=song.title,
                artist=song.artist,
                duration=song.duration,
                size=song.size,
                album=song.album,
                genre=song.genre,
                image=image,
                audio=audio,
            )

            created_song.save()

            return created_song

        except Exception as e:

            print(f"Error al guardar la cancion {e}")
            return None

    @staticmethod
    def stream_song(song_key: SongKey, rang: tuple[int, int] = None):
        """"""
        try:
            title, artist = song_key.key
            song: Song = Song.objects.get(title=title, artist=artist)

            audio_file: FieldFile = song.audio.open("rb")
            file_size: int = audio_file.size

            start = rang[0] if rang[0] else 0
            end = rang[1] if rang[1] else file_size - 1

            length: int = end - start + 1

            audio_file.seek(start)

            def file_iterator(
                file: FieldFile,
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

            return file_iterator(audio_file, length), file_size

        except Song.DoesNotExist:
            write_log("Song no encontrada", 3)
            return None, None
