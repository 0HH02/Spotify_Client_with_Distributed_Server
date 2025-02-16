from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status
from ..distributed_layer.distributed_interface import DistributedInterface
from ..distributed_layer.song_dto import SongKey


class FindStreamersView(APIView):
    def get(self, request: Request, __=None) -> Response:
        song_id: str | None = request.query_params.get("song_id")
        if not song_id:
            return Response(
                {"Error": "The query param song_id is not especified"},
                status.HTTP_400_BAD_REQUEST,
            )
        print(song_id)

        song_key: SongKey | None = SongKey.from_string(song_id)

        if not song_key:
            return Response(
                {"Error": "The song_id param is not in a correct format"},
                status.HTTP_400_BAD_REQUEST,
            )

        distributed_interface = DistributedInterface()
        streamers, active_nodes = distributed_interface.search_song_streamers(song_key)

        return Response(
            {
                "data": {
                    "streamers": [n.to_dict() for n in streamers],
                    "nodes": [n.to_dict() for n in active_nodes],
                },
            },
            status.HTTP_200_OK,
        )
