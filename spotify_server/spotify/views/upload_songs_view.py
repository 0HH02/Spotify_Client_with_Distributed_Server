# music/views/upload_song_view.py
import os
import json
from uuid import uuid4

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request
from django.conf import settings


class UploadSongView(APIView):
    def post(self, request: Request, format=None) -> Response:
        """"""
