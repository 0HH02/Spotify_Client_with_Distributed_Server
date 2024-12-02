from django.db.models.manager import BaseManager
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status

from ..models import Song
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
        result = []
        for s in songs:
            result.append(s.to_dict_metadata())

        return Response({"data": result}, status=status.HTTP_200_OK)
