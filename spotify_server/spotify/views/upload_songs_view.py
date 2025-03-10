# music/views/upload_song_view.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.serializers import ValidationError
from rest_framework.request import Request

from ..decoders.mp3_decoder import Mp3Decoder
from ..distributed_layer.distributed_interface import DistributedInterface
from ..distributed_layer.distributed_interface import SongDto
from ..logs import write_log


class UploadSongView(APIView):
    def post(self, request: Request, _=None) -> Response:
        """"""
        try:
            file = request.FILES.get("file")
            if file:
                file_bytes: bytes = file.read()
                song_data: dict = Mp3Decoder.decode(file_bytes)
                write_log("song data obtained", 2)
                song_dto: SongDto | None = SongDto.from_dict(song_data)
                write_log("song dto created", 2)
                if song_dto:
                    distributed_interface = DistributedInterface()
                    write_log("calling kademlia", 2)
                    succes, active_nodes = distributed_interface.store_song(song_dto)
                    if succes:
                        return Response(
                            {
                                "data": {"nodes": [n.to_dict() for n in active_nodes]},
                            },
                            status.HTTP_200_OK,
                        )
                    return Response(
                        {"error": "Error uploading the song"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

                return Response(
                    {"error": "Failed to decode the song data"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except ValidationError:
            return Response(
                {"error": "file format not suported"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except ValueError:
            return Response(
                {"error": "missing metadata or file encoding not suported"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response({"error": e}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
