from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status


from ..logs import write_log
from ..distributed_layer.distributed_interface import DistributedInterface


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
        write_log("Getting all", 2)
        distributed_interface = DistributedInterface()
        result, active_nodes = distributed_interface.get_all_songs()

        return Response(
            {
                "data": {
                    "songs": [s.to_dict() for s in result],
                    "nodes": [n.to_dict() for n in active_nodes],
                }
            },
            status=status.HTTP_200_OK,
        )
