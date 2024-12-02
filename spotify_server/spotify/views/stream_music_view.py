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

        generator = SongServices.stream_song(
            music_id,
            (range_match.group(1), range_match.group(2)) if range_match else None,
        )

        if generator:
            response = StreamingHttpResponse(
                generator,
                status=206,
                content_type="audio/mpeg",
            )
            # response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
            # response["Accept-Ranges"] = "bytes"
            # response["Content-Length"] = str(length)
            return response

        return Response(
            {"error": "Music not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

        # try:
        #     # Cargar los metadatos desde el archivo JSON
        #     with open("metadata.json", "r", encoding="utf-8") as f:
        #         data = json.load(f)

        #     # Buscar la música por ID
        #     music = next((c for c in data["music"] if c["id"] == music_id), None)

        #     if not music:
        #         return Response(
        #             {"error": "Music not found."},
        #             status=status.HTTP_404_NOT_FOUND,
        #         )

        #     music_path = os.path.join(settings.MEDIA_ROOT, music["root"])

        #     if not os.path.exists(music_path):
        #         return Response(
        #             {"error": "Music file not found."},
        #             status=status.HTTP_404_NOT_FOUND,
        #         )

        #     file_size = os.path.getsize(music_path)
        #     range_header = request.headers.get("Range", "").strip()
        #     range_match = re.match(r"bytes=(\d+)-(\d*)", range_header)

        #     if range_match:
        #         # Manejar solicitud de rango
        #         start = int(range_match.group(1))
        #         end = (
        #             int(range_match.group(2)) if range_match.group(2) else file_size - 1
        #         )
        #         end = min(end, file_size - 1)
        #         length = end - start + 1

        #         # Abrir el archivo y posicionarse en el inicio
        #         file_handle = open(music_path, "rb")
        #         file_handle.seek(start)

        #         # Generador para el streaming
        #         def file_iterator(file, length, chunk_size=settings.STREAM_CHUNK_SIZE):
        #             bytes_remaining = length
        #             while bytes_remaining > 0:
        #                 read_size = min(chunk_size, bytes_remaining)
        #                 data = file.read(read_size)
        #                 if not data:
        #                     break
        #                 yield data
        #                 bytes_remaining -= len(data)

        #         response = StreamingHttpResponse(
        #             file_iterator(file_handle, length, settings.STREAM_CHUNK_SIZE),
        #             status=206,
        #             content_type="audio/mpeg",
        #         )
        #         response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
        #         response["Accept-Ranges"] = "bytes"
        #         response["Content-Length"] = str(length)
        #         return response

        #     else:
        #         # Enviar todo el archivo como un stream
        #         file_handle = open(music_path, "rb")

        #         # Generador para el streaming del archivo completo
        #         def file_iterator(file, chunk_size=settings.STREAM_CHUNK_SIZE):
        #             while True:
        #                 data = file.read(chunk_size)
        #                 if not data:
        #                     break
        #                 yield data

        #         response = StreamingHttpResponse(
        #             file_iterator(file_handle, settings.STREAM_CHUNK_SIZE),
        #             status=200,
        #             content_type="audio/mpeg",
        #         )
        #         response["Content-Length"] = str(file_size)
        #         response["Accept-Ranges"] = "bytes"
        #         return response

        # except Exception as e:
        #     return Response(
        #         {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        #     )
