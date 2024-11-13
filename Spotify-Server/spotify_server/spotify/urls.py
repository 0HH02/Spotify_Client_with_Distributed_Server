# music/urls.py

from django.urls import path
from .views import StreamMusicView, ListSongsView, SearchSongsView, UploadSongView

urlpatterns = [
    path("stream/<int:music_id>/", StreamMusicView.as_view(), name="music-stream"),
    path("songs/", ListSongsView.as_view(), name="list-songs"),
    path("search/", SearchSongsView.as_view(), name="search-songs"),
    path("upload/", UploadSongView.as_view(), name="upload-song"),
]
