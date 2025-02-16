"""
This module contains the SearchSongsView class that handles the search of songs 
based on a query and a searchBy parameter.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request

from ..distributed_layer.distributed_interface import DistributedInterface


class SearchSongsView(APIView):
    def get(self, request: Request, _=None) -> Response:

        search_by: str | None = request.query_params.get("searchBy")
        query: str = request.query_params.get("query").lower()

        if search_by not in ["title", "gender", "artist", "album"]:
            return Response(
                {
                    "error": "El parámetro 'searchBy' debe ser 'title', 'gender', 'artist' o 'album'."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        distributed_interface = DistributedInterface()

        songs, active_nodes = distributed_interface.search_songs_by(search_by, query)
        result = [n.to_dict() for n in songs]

        return Response(
            {
                "data": {
                    "songs": result,
                    "nodes": [n.to_dict() for n in active_nodes],
                }
            },
            status.HTTP_200_OK,
        )
