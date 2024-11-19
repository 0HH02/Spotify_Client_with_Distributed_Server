# music/views/upload_song_view.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import os
import json
from uuid import uuid4


class UploadSongView(APIView):
    def post(self, request, format=None):
        try:
            # Obtener el archivo de audio y los metadatos de la solicitud
            audio_file = request.FILES.get("audio")
            title = request.data.get("title")

            artist = request.data.get("artist")
            artist = json.loads(artist) if artist else ["Unknown Artist"]

            gender = request.data.get("gender")
            gender = json.loads(gender) if gender else ["Unknown Gender"]

            album = request.data.get("album")
            image_url = request.data.get("imageUrl")

            # Validar que los campos requeridos estén presentes
            if not all([audio_file, title]):
                return Response(
                    {"error": "Metadata fields are missing."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validar que el archivo sea MP3
            if audio_file.content_type != "audio/mpeg":
                return Response(
                    {"error": "Only MP3 files are supported."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Generar un nombre de archivo único
            song_id = uuid4().hex
            song_filename = f"{song_id}.mp3"
            song_path = os.path.join(settings.MEDIA_ROOT, "music", song_filename)

            # Guardar el archivo MP3 directamente
            with open(song_path, "wb") as f:
                for chunk in audio_file.chunks():
                    f.write(chunk)

            # Guardar los metadatos en metadata.json
            metadata_path = os.path.join(settings.BASE_DIR, "metadata.json")
            new_song = {
                "id": song_id,
                "title": title,
                "artist": (artist if isinstance(artist, list) else [artist]),
                "gender": (gender if isinstance(gender, list) else [gender]),
                "album": album if album else "Unknown Album",
                "root": f"music/{song_filename}",
                "imageUrl": image_url,
            }

            # Leer el archivo JSON y agregar la nueva canción
            if os.path.exists(metadata_path):
                with open(metadata_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {"music": []}

            data["music"].append(new_song)

            # Escribir los datos actualizados en el archivo JSON
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            return Response(
                {"message": "Upload successful."},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
