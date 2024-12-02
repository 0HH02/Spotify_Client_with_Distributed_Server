import threading
import subprocess
import time
from queue import Queue, Empty
import pyaudio
import requests
import streamlit as st

# Define constantes
CHUNK_SIZE = 8192
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
URL = "http://192.168.167.209:8000/api"


# Clase AudioBuffer
class AudioBuffer:
    def __init__(self, max_size=200):
        self.buffer = Queue(maxsize=max_size)

    def append(self, data):
        try:
            self.buffer.put(data, timeout=1)
        except:
            pass  # Ignorar si el buffer está lleno

    def pop(self, timeout=None):
        try:
            return self.buffer.get(timeout=timeout)
        except Empty:
            return None

    def clear(self):
        while not self.buffer.empty():
            try:
                self.buffer.get_nowait()
            except Empty:
                break

    def __len__(self):
        return self.buffer.qsize()


# Clase AudioStreamer
class AudioStreamer:
    def __init__(self, endpoints, buffer: AudioBuffer, max_retries=3):
        self.endpoints = endpoints
        self.buffer = buffer
        self.current_endpoint_index = 0
        self.stop_event = threading.Event()
        self.byte_position = 0
        self.max_retries = max_retries
        self.retry_count = 0
        self.finished = False  # Indica si la descarga ha terminado

    def run(self):
        print("[Streamer] Hilo de descarga iniciado")
        while not self.stop_event.is_set() and not self.finished:
            endpoint = self.endpoints[self.current_endpoint_index]
            headers = {"Range": f"bytes={self.byte_position}-"}
            try:
                print(
                    f"[Streamer] Conectando a {endpoint} desde el byte {self.byte_position}"
                )
                with requests.get(
                    endpoint, headers=headers, stream=True, timeout=5
                ) as response:
                    if response.status_code == 206:  # Descarga parcial
                        self.retry_count = 0
                        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                            if self.stop_event.is_set():
                                print("[Streamer] Detenido durante la descarga.")
                                break
                            if chunk:
                                self.buffer.append(chunk)
                                self.byte_position += len(chunk)
                                print(
                                    f"[Streamer] Bytes descargados: {self.byte_position} - {self.byte_position + len(chunk)}"
                                )
                        # Marcar como terminado y enviar centinela
                        self.finished = True
                        self.buffer.append(None)  # Centinela para indicar fin de datos
                        print("[Streamer] Descarga completada.")
                    elif response.status_code == 200:  # Descarga completa sin rango
                        print("[Streamer] Archivo completo descargado.")
                        self.finished = True
                        self.buffer.append(None)  # Centinela para indicar fin de datos
                    else:
                        print(
                            f"[Streamer] Respuesta inesperada: {response.status_code}"
                        )
                        self.switch_endpoint()
            except requests.RequestException as e:
                print(f"[Streamer] Error al conectar con {endpoint}: {e}")
                self.switch_endpoint()
            time.sleep(1)
        print("[Streamer] Hilo de descarga finalizado")

    def switch_endpoint(self):
        self.retry_count += 1
        if self.retry_count >= self.max_retries:
            self.retry_count = 0
            self.current_endpoint_index = (self.current_endpoint_index + 1) % len(
                self.endpoints
            )
            print(
                f"[Streamer] Cambiando al siguiente endpoint: {self.endpoints[self.current_endpoint_index]}"
            )
        else:
            print(
                f"[Streamer] Reintentando el mismo endpoint: {self.retry_count}/{self.max_retries}"
            )

    def stop(self):
        self.stop_event.set()
        print("[Streamer] Señal de parada enviada")
        self.buffer.append(None)  # Para desbloquear buffer.pop()


# Clase AudioPlayer con métodos de pausa y reanudación
class AudioPlayer:
    def __init__(self, buffer):
        self.buffer = buffer
        self.pcm_buffer = Queue(maxsize=200)
        self.pyaudio_instance = pyaudio.PyAudio()
        self.stream = self.pyaudio_instance.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            output=True,
            frames_per_buffer=CHUNK_SIZE,
        )
        self.stop_event = threading.Event()
        self.finished = False  # Indica si la reproducción ha terminado
        self.pause_event = threading.Event()  # Evento para pausar la reproducción
        self.process = subprocess.Popen(
            [
                "ffmpeg",
                "-i",
                "pipe:0",
                "-f",
                "s16le",
                "-acodec",
                "pcm_s16le",
                "-ac",
                str(CHANNELS),
                "-ar",
                str(RATE),
                "-",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=10 * CHUNK_SIZE,
        )
        print("[Player] AudioPlayer inicializado")

    def feed_ffmpeg_stdin(self):
        print("[Player] Hilo feed_ffmpeg_stdin iniciado")
        while not self.stop_event.is_set():
            try:
                chunk = self.buffer.pop(timeout=1)
                if chunk is None:
                    # Centinela recibido, cerrar stdin de FFmpeg
                    print("[Player] Centinela recibido. Cerrando stdin de FFmpeg.")
                    self.process.stdin.close()
                    break
                if chunk:
                    self.process.stdin.write(chunk)
            except Exception as e:
                print(f"[Player] Error al escribir en ffmpeg stdin: {e}")
                break
        print("[Player] Hilo feed_ffmpeg_stdin finalizado")

    def read_ffmpeg_stdout(self):
        print("[Player] Hilo read_ffmpeg_stdout iniciado")
        while not self.stop_event.is_set():
            try:
                pcm_data = self.process.stdout.read(CHUNK_SIZE)
                if pcm_data:
                    self.pcm_buffer.put(pcm_data)
                else:
                    if self.process.poll() is not None:
                        # FFmpeg ha terminado
                        print("[Player] FFmpeg ha terminado de procesar.")
                        break
                    else:
                        time.sleep(0.01)
            except Exception as e:
                print(f"[Player] Error al leer de ffmpeg stdout: {e}")
                break
        print("[Player] Hilo read_ffmpeg_stdout finalizado")

    def run(self):
        print("[Player] Iniciando hilos de FFmpeg")
        self.feed_thread = threading.Thread(target=self.feed_ffmpeg_stdin, daemon=True)
        self.read_thread = threading.Thread(target=self.read_ffmpeg_stdout, daemon=True)

        self.feed_thread.start()
        self.read_thread.start()
        print("[Player] Hilos de FFmpeg iniciados")

        while not self.stop_event.is_set():
            if self.pause_event.is_set():
                time.sleep(0.1)
                continue
            try:
                pcm_chunk = self.pcm_buffer.get(timeout=1)
                if pcm_chunk:
                    self.stream.write(pcm_chunk)
                else:
                    if self.process.poll() is not None and self.pcm_buffer.empty():
                        self.finished = True
                        print("[Player] Reproducción completada.")
                        break
            except Empty:
                # Verificar si FFmpeg ha terminado y los buffers están vacíos
                if self.process.poll() is not None and self.pcm_buffer.empty():
                    self.finished = True
                    print("[Player] Reproducción completada.")
                    break
                else:
                    continue
            except Exception as e:
                print(f"[Player] Error al reproducir audio: {e}")
                break

        # Señal de que la reproducción ha detenido
        print("[Player] Señal de parada detectada. Cerrando hilos y procesos.")
        self.stop_event.set()

        # Esperar a que los hilos terminen
        self.feed_thread.join(timeout=2)
        self.read_thread.join(timeout=2)

        # Terminar el proceso de FFmpeg si aún está en ejecución
        if self.process.poll() is None:
            print("[Player] Terminando proceso FFmpeg")
            self.process.terminate()
            self.process.wait(timeout=5)

        # Cerrar el stream de PyAudio
        try:
            self.stream.stop_stream()
            self.stream.close()
            self.pyaudio_instance.terminate()
            print("[Player] PyAudio cerrado exitosamente")
        except Exception as e:
            print(f"[Player] Error al cerrar PyAudio: {e}")

        self.finished = True
        print("[Player] AudioPlayer finalizado")

    def stop(self):
        if not self.stop_event.is_set():
            self.stop_event.set()
            self.pause_event.clear()  # Asegurarse de no estar en pausa
            print("[Player] Deteniendo AudioPlayer")
            try:
                self.process.stdin.close()
            except Exception:
                pass
            try:
                self.process.terminate()
            except Exception:
                pass
            print("[Player] FFmpeg terminado y streams cerrados")


# Función principal
def main():
    st.title("Interfaz de Consola Tipo Spotify")

    # Inicializar variables de estado de sesión para el reproductor
    if "player" not in st.session_state:
        st.session_state.player = None
    if "streamer" not in st.session_state:
        st.session_state.streamer = None
    if "player_thread" not in st.session_state:
        st.session_state.player_thread = None
    if "streamer_thread" not in st.session_state:
        st.session_state.streamer_thread = None
    if "playback_status" not in st.session_state:
        st.session_state.playback_status = "stopped"  # 'stopped', 'playing', 'paused'

    # Funciones para el control de reproducción
    def start_playback(song_id):
        print(song_id)
        # Siempre detener la reproducción actual antes de iniciar una nueva
        stop_playback()
        # Iniciar nueva reproducción
        ENDPOINTS = [f"{URL}/stream/{song_id}/"]
        audio_buffer = AudioBuffer(max_size=200)
        streamer = AudioStreamer(ENDPOINTS, audio_buffer)
        player = AudioPlayer(audio_buffer)

        streamer_thread = threading.Thread(target=streamer.run, daemon=True)
        player_thread = threading.Thread(target=player.run, daemon=True)

        streamer_thread.start()
        player_thread.start()

        # Guardar en el estado de sesión
        st.session_state.streamer = streamer
        st.session_state.player = player
        st.session_state.streamer_thread = streamer_thread
        st.session_state.player_thread = player_thread
        st.session_state.playback_status = "playing"
        st.success("🎶 Reproducción iniciada.")

    def stop_playback():
        if st.session_state.player and st.session_state.streamer:
            try:
                st.session_state.player.stop()
                st.session_state.streamer.stop()
                # Esperar a que los hilos terminen
                st.session_state.player_thread.join()
                st.session_state.streamer_thread.join()
                # Limpiar el buffer
                st.session_state.player.buffer.clear()
                # Restablecer el estado
                st.session_state.player = None
                st.session_state.streamer = None
                st.session_state.player_thread = None
                st.session_state.streamer_thread = None
                st.session_state.playback_status = "stopped"
                st.info("⏹️ Reproducción detenida.")
            except Exception as e:
                st.error(f"❌ Error al detener la reproducción: {e}")
        else:
            st.warning("⚠️ No hay reproducción para detener.")

    def get_filtered_mp3_files():
        return (
            st.session_state.filtered_mp3_files
            if "filtered_mp3_files" in st.session_state
            else []
        )

    def list_songs():
        response = requests.get(f"{URL}/songs")
        if response and response.status_code == 200:
            return response.json()["music"]
        else:
            return []

    def search_songs(search_by, query):
        response = requests.get(
            f"{URL}/search/",
            params={"searchBy": search_by, "query": query},
        )
        if response and response.status_code == 200:
            return response.json()["results"]
        else:
            return []

    # Barra lateral para búsqueda y subida
    st.sidebar.title("Opciones")
    # Sección de subida
    st.sidebar.subheader("Subir Canción")
    uploaded_file = st.sidebar.file_uploader("Selecciona un archivo MP3", type=["mp3"])
    if uploaded_file is not None:
        # Enviar el archivo al endpoint /api/upload/
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "audio/mpeg")}
        try:
            response = requests.post(f"{URL}/upload/", files=files)
            if response.status_code == 201:
                st.sidebar.success("🎵 Canción subida exitosamente.")
                # Opcionalmente, refrescar la lista de canciones
                st.session_state.filtered_mp3_files = list_songs()
            else:
                st.sidebar.error(f"Error al subir la canción: {response.status_code}")
        except Exception as e:
            st.sidebar.error(f"Error al enviar la canción: {e}")

    st.sidebar.subheader("Buscar Canciones")
    enable_filter = st.sidebar.checkbox("Habilitar Filtros", value=False)

    if enable_filter:
        search_query = st.sidebar.text_input(
            "Buscar una canción", key="search_song_input"
        )
        search_by = st.sidebar.selectbox(
            "Buscar por", ["title", "gender", "artist", "album"]
        )

        if search_query:
            if (
                "search_query" not in st.session_state
                or st.session_state.search_query != search_query
            ):
                if (
                    "filtered_mp3_files" not in st.session_state
                    or st.session_state.search_query != search_query
                ):
                    filtered_mp3_files = search_songs(search_by, search_query)
                    st.session_state.filtered_mp3_files = filtered_mp3_files
                    st.session_state.search_query = search_query
                else:
                    filtered_mp3_files = get_filtered_mp3_files()
            filtered_mp3_files = get_filtered_mp3_files()
        else:
            filtered_mp3_files = get_filtered_mp3_files()
    else:
        if "filtered_mp3_files" not in st.session_state:
            st.session_state.filtered_mp3_files = list_songs()
        st.session_state.search_query = ""
        filtered_mp3_files = get_filtered_mp3_files()

    st.header("Todas las Canciones:")

    if "current_song_index" not in st.session_state:
        st.session_state.current_song_index = 0

    current_song_index = st.session_state.current_song_index

    st.sidebar.title("Playlist")
    if filtered_mp3_files:

        def get_song_display_string(song):
            return f"{song['id']}: {song['title']} by {', '.join(song['artist'])}"

        song_options = [get_song_display_string(song) for song in filtered_mp3_files]
        song_selection = st.radio(
            "Selecciona una canción", song_options, index=current_song_index
        )

        # Verificar si la selección de canción ha cambiado
        if song_selection != get_song_display_string(
            filtered_mp3_files[current_song_index]
        ):
            # Actualizar el índice de la canción actual
            st.session_state.current_song_index = song_options.index(song_selection)
            st.session_state.current_stream_position = 0
            # Detener cualquier reproducción antes de iniciar una nueva
            stop_playback()
            selected_song = filtered_mp3_files[st.session_state.current_song_index]
            start_playback(selected_song["id"])
        else:
            selected_song = filtered_mp3_files[current_song_index]

        # Mostrar controles de reproducción
        st.success(
            f"Reproduciendo: {selected_song['title']} by {', '.join(selected_song['artist'])}"
        )

        col1, col2, col3 = st.columns(3)

        with col2:
            if st.button("⏹️ Detener", key="stop_playback"):
                stop_playback()

        with col3:
            if st.button("⏭️ Siguiente", key="next_button"):
                if current_song_index < len(filtered_mp3_files) - 1:
                    st.session_state.current_song_index += 1
                    stop_playback()
                    selected_song = filtered_mp3_files[
                        st.session_state.current_song_index
                    ]
                    start_playback(selected_song["id"])

        # Mostrar estado de reproducción actual
        st.write(
            f"**Estado de Reproducción:** {st.session_state.playback_status.capitalize()}"
        )

        # Monitorear la finalización de la reproducción
        if st.session_state.player is not None and st.session_state.player.finished:
            stop_playback()
            st.info("🎵 La canción ha terminado de reproducirse.")

    else:
        st.warning("No se encontraron canciones.")


if __name__ == "__main__":
    main()
