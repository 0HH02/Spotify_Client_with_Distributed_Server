import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import StreamingHttpResponse
from ..services.song_services import SongServices


class StreamMusicView(APIView):
    def get(self, request, music_id, _=None):

        range_header = request.headers.get("Range", "").strip()
        range_match = re.match(r"bytes=(\d+)-(\d*)", range_header)

        start = int(range_match.group(1)) if range_match else None
        end = (
            int(range_match.group(2)) if range_match and range_match.group(2) else None
        )

        generator, file_size = SongServices.stream_song(
            music_id,
            (start, end),
        )

        end = end if end else file_size - 1

        length = end - start + 1 if range_match else file_size

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
