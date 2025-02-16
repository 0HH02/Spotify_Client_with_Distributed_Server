import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import StreamingHttpResponse
from ..distributed_layer.distributed_interface import DistributedInterface
from ..distributed_layer.song_dto import SongKey


class StreamMusicView(APIView):
    def get(self, request, _=None):
        music_id: str | None = request.query_params.get("song_id")
        range_header = request.headers.get("Range", "").strip()
        range_match = re.match(r"bytes=(\d+)-(\d*)", range_header)

        start = int(range_match.group(1)) if range_match else None
        end = (
            int(range_match.group(2)) if range_match and range_match.group(2) else None
        )

        distributed_interface = DistributedInterface()

        generator, file_size = distributed_interface.stream_song(
            SongKey.from_string(music_id), (start, end)
        )

        end: int = end if end else file_size - 1

        length: int = end - start + 1 if range_match else file_size

        if generator:
            response = StreamingHttpResponse(
                generator,
                status=206,
                content_type="audio/mpeg",
            )
            response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
            response["Accept-Ranges"] = "bytes"
            response["Content-Length"] = str(length)
            response["Access-Control-Allow-Origin"] = "*"
            return response

        return Response(
            {"error": "Music not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
