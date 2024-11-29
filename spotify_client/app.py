import streamlit as st
import requests
import random
from flask import Flask, request, redirect
from requests.exceptions import ConnectionError, Timeout, RequestException
import threading

BASE_URLS = [
    "http://192.168.1.104:8000/api",  # Primary server
    "http://192.168.1.105:8000/api",  # Backup server 1
    "http://192.168.1.106:8080/api",  # Backup server 2
]


class ResilientRequestMiddleware:
    def __init__(self, base_urls):
        self.base_urls = base_urls

    def get_url(self, endpoint, params=None):
        for base_url in self.base_urls:
            try:
                response = requests.get(f"{base_url}/{endpoint}", params=params)
                if response.status_code == 200:
                    return response
            except (ConnectionError, Timeout, RequestException):
                print(f"Error connecting to {base_url}")
                continue
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")
        return None

    def get_stream_url(self, song_id):
        for base_url in self.base_urls:
            try:
                print(f"Trying {base_url} and url {base_url}/stream/{song_id}/")
                response = requests.get(f"{base_url}/stream/{song_id}/")
                if response.status_code == 200 or response.status_code == 206:
                    return f"{base_url}/stream/{song_id}/"
            except (ConnectionError, Timeout, RequestException):
                continue
        return None


# Instantiate middleware
resilient_middleware = ResilientRequestMiddleware(BASE_URLS)

app = Flask(__name__)


@app.route("/stream", methods=["GET"])
def get_stream_url():
    song_id = request.args.get("song_id")
    stream_url = resilient_middleware.get_stream_url(song_id)
    print("stream_url: ", stream_url)
    if stream_url:
        return redirect(stream_url)
    else:
        return "", 503


@app.route("/songs", methods=["GET"])
def list_songs_endpoint():
    response = resilient_middleware.get_url("songs")

    if response and response.status_code == 200:
        return response.json(), 200
    else:
        return "", 503


@app.route("/search", methods=["GET"])
def search_songs_endpoint():
    search_by = request.args.get("searchBy")
    query = request.args.get("query")
    response = resilient_middleware.get_url(
        "search", params={"searchBy": search_by, "query": query}
    )
    if response and response.status_code == 200:
        return response.json(), 200
    else:
        return "", 503


def run_flask():
    app.run(port=5000)


def get_filtered_mp3_files():
    return (
        st.session_state.filtered_mp3_files
        if "filtered_mp3_files" in st.session_state
        else []
    )


def list_songs():
    response = requests.get("http://localhost:5000/songs")
    if response and response.status_code == 200:
        return response.json()["music"]
    else:
        return []


def search_songs(search_by, query):
    response = requests.get(
        "http://localhost:5000/search/", params={"searchBy": search_by, "query": query}
    )
    if response and response.status_code == 200:
        return response.json()["results"]
    else:
        return []


def main():
    st.title("Spotify Clone Console Interface")

    # Sidebar for search
    st.sidebar.title("Search Songs")
    enable_filter = st.sidebar.checkbox("Enable Filters", value=False)

    if enable_filter:
        search_query = st.sidebar.text_input(
            "Search for a song", key="search_song_input"
        )
        search_by = st.sidebar.selectbox(
            "Search by", ["title", "gender", "artist", "album"]
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

    st.header("All Songs:")

    if "current_song_index" not in st.session_state:
        st.session_state.current_song_index = 0

    current_song_index = st.session_state.current_song_index

    st.sidebar.title("Playlist")
    if filtered_mp3_files:
        song_selection = st.radio(
            "Select a song",
            [
                f"{song['id']}: {song['title']} by {', '.join(song['artist'])}"
                for song in filtered_mp3_files
            ],
            index=current_song_index,
        )
        selected_song = filtered_mp3_files[current_song_index]

        if song_selection != filtered_mp3_files[current_song_index]:
            st.session_state.current_song_index = next(
                (
                    i
                    for i, song in enumerate(filtered_mp3_files)
                    if f"{song['id']}: {song['title']} by {', '.join(song['artist'])}"
                    == song_selection
                ),
                0,
            )
            st.session_state.current_stream_position = 0

        # Handle audio playback with resiliency using proxy endpoint
        st.audio(
            f"http://localhost:5000/stream?song_id={selected_song["id"]}",
            format="audio/mp3",
        )

        st.success(
            f"Currently Playing: {selected_song['title']} by {', '.join(selected_song['artist'])}"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⏪ Previous") and current_song_index > 0:
                st.session_state.current_song_index -= 1
                st.session_state.current_stream_position = 0
                st.session_state.is_playing = False
        with col2:
            if (
                st.button("⏩ Next")
                and current_song_index < len(filtered_mp3_files) - 1
            ):
                st.session_state.current_song_index += 1
                st.session_state.current_stream_position = 0
                st.session_state.is_playing = False
    else:
        st.warning("No songs found.")


if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    main()
