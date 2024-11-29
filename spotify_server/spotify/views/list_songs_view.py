import json
from django.db.models.manager import BaseManager
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status

from ..models import Song
from ..serializers import SongMetadataSerializer
from ..services.song_services import SongServices


class ListSongsMetadataView(APIView):
    """
    ListSongsMetadataView is a Django Rest Framework APIView that handles GET requests to retrieve metadata for all songs.

    Methods:
        get(self, _: Request, __=None):
            Handles GET requests to retrieve metadata for all songs.
            Returns a JSON response containing serialized song metadata with HTTP status 200 OK.
    """

    def get(self, _: Request, __=None):
        """
        Handles GET requests to retrieve all songs metadata.

        Args:
            _: Request object (not used).
            __: Optional additional parameter (not used).

        Returns:
            Response: A Response object containing serialized song metadata and an HTTP 200 status code.
        """
        songs: BaseManager[Song] = SongServices.get_all_songs_metadata()
        songs_serialized: SongMetadataSerializer = SongMetadataSerializer(
            songs, many=True
        )
        return Response({"data": songs_serialized.data}, status=status.HTTP_200_OK)

        # try:
        #     # Leer el archivo JSON de metadatos
        #     with open("metadata.json", "r", encoding="utf-8") as f:
        #         data = json.load(f)

        #     # Crear una nueva lista de canciones sin el campo 'root'
        #     musics = []
        #     for cancion in data["music"]:
        #         cancion_sin_root = {
        #             "id": cancion["id"],
        #             "title": cancion["title"],
        #             "artist": cancion["artist"],
        #             "gender": cancion["gender"],
        #             "album": cancion["album"],
        #             "imageUrl": cancion["imageUrl"],
        #         }
        #         musics.append(cancion_sin_root)

        #     # Retornar las canciones en formato JSON
        #     return Response({"music": musics}, status=status.HTTP_200_OK)

        # except FileNotFoundError:
        #     return Response(
        #         {"error": "Metadata file not found."},
        #         status=status.HTTP_404_NOT_FOUND,
        #     )
        # except Exception as e:
        #     return Response(
        #         {"error": str(e)},
        #         status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #     )
