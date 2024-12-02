# music/views/upload_song_view.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.serializers import ValidationError
from rest_framework.request import Request

from ..services.song_services import SongServices


class UploadSongView(APIView):
    def post(self, request: Request, _=None) -> Response:
        """"""
        try:
            file = request.FILES.get("file")
            if file:
                new_song = SongServices.upload_song(file)
                return Response(
                    {"data": new_song.to_dict_metadata()}, status=status.HTTP_200_OK
                )

        except ValidationError:
            return Response(
                {"error": "file format not suported"},
                status=status.HTTP_400_BAD_REQUEST,
            )
