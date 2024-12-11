import requests
import pydub
import pydub.playback
import io

from pydub import AudioSegment
from pydub.playback import play


# URL base del backend (ajústala si es necesario)
BASE_URL = "http://192.168.159.209:8000/api"


# Funciones para interactuar con el backend
def list_songs():
    response = requests.get(f"{BASE_URL}/songs/")
    if response.status_code == 200:
        songs = response.json()
        print("\nLista de Canciones:")
        for song in songs["music"]:
            print(f"{song['id']}: {song['title']} by {', '.join(song['artist'])}")
    else:
        print("Error al listar canciones.")


def search_songs(search_by, query):
    response = requests.get(
        f"{BASE_URL}/search/", params={"searchBy": search_by, "query": query}
    )
    if response.status_code == 200:
        results = response.json()
        print(f"\nResultados de búsqueda para '{query}' por {search_by}:")
        if not results["results"]:
            print("No se encontraron resultados.")
            return
        for song in results["results"]:
            print(f"{song['id']}: {song['title']} by {', '.join(song['artist'])}")
    else:
        print("Error en la búsqueda de canciones.")


def save_song(song_id):
    response = requests.post(f"{BASE_URL}/songs/{song_id}/save/")
    if response.status_code == 200:
        print(f"\nCanción '{response.json()['title']}' guardada con éxito.")
    else:
        print("Error al guardar la canción.")


def play_song(song_id):
    url = f"{BASE_URL}/stream/{song_id}/"
    response = requests.get(url, stream=True)

    if response.status_code == 200:
        # Leer el contenido del stream
        audio_data = io.BytesIO(response.content)

        # Cargar el audio en un AudioSegment
        audio = AudioSegment.from_file(
            audio_data, format="mp3"
        )  # Cambia 'mp3' al formato adecuado

        # Reproducir el audio
        play(audio)
    else:
        print(f"Error en la transmisión: {response.status_code}")


# Menú de la consola
def main():
    print("Bienvenido a la consola de música")
    while True:
        print("\nOpciones:")
        print("1. Listar canciones")
        print("2. Buscar canción")
        print("3. Guardar canción")
        print("4. Reproducir canción")
        print("5. Salir")
        choice = input("Seleccione una opción: ")

        if choice == "1":
            list_songs()
        elif choice == "2":
            search_by = input(
                "Ingrese el tipo de búsqueda (title, gender, artist, album): "
            )
            query = input("Qué quiere buscar:")
            search_songs(search_by, query)
        elif choice == "3":
            song_id = input("Ingrese el ID de la canción para guardar: ")
            save_song(song_id)
        elif choice == "4":
            song_id = input("Ingrese el ID de la canción para reproducir: ")
            play_song(song_id)
        elif choice == "5":
            print("Saliendo de la consola de música. ¡Hasta luego!")
            break
        else:
            print("Opción inválida, por favor intente nuevamente.")


# Ejecutar la interfaz de consola
if __name__ == "__main__":
    main()


# PS C:\HH\Escuela\Distribuido\Proyecto> git push
# Enumerating objects: 11765, done.
# Counting objects: 100% (11765/11765), done.
# Delta compression using up to 24 threads
# Compressing objects: 100% (8151/8151), done.
# Writing objects: 100% (11764/11764), 70.67 MiB | 399.83 MiB/s, done.
# Total 11764 (delta 2355), reused 11758 (delta 2353), pack-reused 0 (from 0)
# error: RPC failed; HTTP 400 curl 22 The requested URL returned error: 400
# send-pack: unexpected disconnect while reading sideband packet
# fatal: the remote end hung up unexpectedly
# Everything up-to-date
