import threading
import queue
import subprocess
import pyaudio


def read_stream(ffmpeg_process, audio_queue, chunk_size):
    while True:
        data = ffmpeg_process.stdout.read(chunk_size)
        if not data:
            break
        audio_queue.put(data)


def play_audio(audio_queue, pyaudio_stream):
    while True:
        try:
            data = audio_queue.get(timeout=1)  # Timeout para evitar bloqueos
            pyaudio_stream.write(data)
        except queue.Empty:
            break


def stream_and_play_music(url):
    ffmpeg_process = subprocess.Popen(
        [
            "ffmpeg",
            "-reconnect",
            "1",
            "-reconnect_streamed",
            "1",
            "-reconnect_delay_max",
            "2",
            "-i",
            url,
            "-f",
            "s16le",
            "-ac",
            "2",
            "-ar",
            "44100",
            "-",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    audio_queue = queue.Queue()
    chunk_size = 4096

    # PyAudio setup
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=2, rate=44100, output=True)

    # Start threads for reading and playing
    threading.Thread(
        target=read_stream, args=(ffmpeg_process, audio_queue, chunk_size)
    ).start()
    play_audio(audio_queue, stream)

    # Clean up
    stream.stop_stream()
    stream.close()
    p.terminate()
    ffmpeg_process.terminate()


# URL del flujo
url = "http://192.168.159.209:8000/api/stream/1/"
stream_and_play_music(url)
