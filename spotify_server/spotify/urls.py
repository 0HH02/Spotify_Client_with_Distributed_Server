# music/urls.py

from django.urls import path
from .views import (
    StreamMusicView,
    ListSongsMetadataView,
    SearchSongsView,
    UploadSongView,
    FindStreamersView,
    AliveView,
)

urlpatterns = [
    path("stream/", StreamMusicView.as_view(), name="music-stream"),
    path("songs/", ListSongsMetadataView.as_view(), name="list-songs"),
    path("search/", SearchSongsView.as_view(), name="search-songs"),
    path("upload/", UploadSongView.as_view(), name="upload-song"),
    path("findStreamers/", FindStreamersView.as_view(), name="find-streamer"),
    path("alive/", AliveView.as_view(), name="alive"),
]
