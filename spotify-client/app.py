import streamlit as st
import os
import pygame

pygame.mixer.init()

mp3_files = [file for file in os.listdir("audio") if file.endswith(".mp3")]
album_art_files = [file for file in os.listdir("audio") if file.endswith(".jpg")]

song_to_album_art = {}
for song in mp3_files:
    song_name = os.path.splitext(song)[0]
    for album_art in album_art_files:
        if song_name in album_art:
            song_to_album_art[song] = album_art


def play_song(song_path):
    pygame.mixer.music.load(song_path)
    pygame.mixer.music.play()


def main():
    st.title("Spotify Clone")

    st.sidebar.title("Search Songs")
    search_query = st.sidebar.text_input("Search for a song")

    filtered_mp3_files = [
        song for song in mp3_files if search_query.lower() in os.path.splitext(song)[0]
    ]

    st.header("All Songs:")

    current_song_index = st.session_state.get("current_song_index", 0)

    st.sidebar.title("Playlist")
    song_selection = st.radio(
        "Select a song", filtered_mp3_files, index=current_song_index
    )

    st.sidebar.audio("audio/" + song_selection, format="audio/mp3", start_time=0)

    get_current_song = filtered_mp3_files[current_song_index]
    album_art_image = song_to_album_art.get(get_current_song, "default.gif")

    album_art_path = "audio/" + album_art_image

    st.sidebar.image(album_art_path, use_column_width=True)

    st.success("Song: " + song_selection)

    if st.button("⏪ Previous") and current_song_index > 0:
        current_song_index -= 1
    elif st.button("⏩ Next") and current_song_index < len(filtered_mp3_files) - 1:
        current_song_index += 1

    st.session_state.current_song_index = current_song_index


if __name__ == "__main__":
    main()
