from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import json


class ListSongsView(APIView):
    def get(self, request, format=None):
        try:
            # Leer el archivo JSON de metadatos
            with open("metadata.json", "r", encoding="utf-8") as f:
                data = json.load(f)

            # Crear una nueva lista de canciones sin el campo 'root'
            musics = []
            for cancion in data["music"]:
                cancion_sin_root = {
                    "id": cancion["id"],
                    "title": cancion["title"],
                    "artist": cancion["artist"],
                    "gender": cancion["gender"],
                    "album": cancion["album"],
                    "imageUrl": cancion["imageUrl"],
                }
                musics.append(cancion_sin_root)

            # Retornar las canciones en formato JSON
            return Response({"music": musics}, status=status.HTTP_200_OK)

        except FileNotFoundError:
            return Response(
                {"error": "Metadata file not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
