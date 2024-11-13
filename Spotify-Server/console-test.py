import requests

# URL base del backend (ajústala si es necesario)
BASE_URL = "http://localhost:8000/api"


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
    response = requests.get(f"{BASE_URL}/stream/{song_id}/")
    if response.status_code == 200:
        print(f"\nReproduciendo '{response.json()['title']}'... (simulado)")
    else:
        print("Error al reproducir la canción.")


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
main()
