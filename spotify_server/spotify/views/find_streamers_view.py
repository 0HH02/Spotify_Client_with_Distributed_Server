from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status


class FindStreamersView(APIView):
    def get(self, _: Request, __=None) -> Response:
        pass
