# music/views/search_songs_view.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import json


class SearchSongsView(APIView):
    def get(self, request, format=None):
        # Obtener parámetros de la solicitud
        search_by = request.query_params.get("searchBy")
        query = request.query_params.get("query", "").lower()

        # Validar que 'searchBy' sea un campo válido
        if search_by not in ["title", "gender", "artist", "album"]:
            return Response(
                {
                    "error": "El parámetro 'searchBy' debe ser 'title', 'gender', 'artist' o 'album'."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Leer el archivo JSON de metadatos
        try:
            with open("metadata.json", "r", encoding="utf-8") as f:
                data = json.load(f)

            # Filtrar canciones basadas en el parámetro 'searchBy' y 'query'
            resultados = []
            for music in data["music"]:
                field = music.get(search_by, [])
                # Convertir a lista para manejar campos que pueden ser listas como 'artist' o 'gender'
                valores = field if isinstance(field, list) else [field]

                # Comprobar coincidencia en cada valor del campo
                for valor in valores:
                    if query in valor.lower():
                        resultados.append(
                            {
                                "id": music["id"],
                                "title": music["title"],
                                "artist": music["artist"],
                                "gender": music["gender"],
                                "album": music["album"],
                                "imageUrl": music["imageUrl"],
                            }
                        )
                        break  # Salir del bucle una vez encontrada una coincidencia en esta canción

            # Devolver los resultados
            return Response({"results": resultados}, status=status.HTTP_200_OK)

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
