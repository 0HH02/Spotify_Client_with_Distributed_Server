import socket
from .kademlia_node import KademliaNode
from .song_dto import SongKey, SongDto


class DistributedInterface:
    _instance: "DistributedInterface" = None
    _distributed_node = None

    def __new__(cls, *_, **__):
        if cls._instance is None:
            ip: str = socket.gethostbyname(socket.gethostname())
            cls._instance = super().__new__(cls)
            cls._distributed_node = KademliaNode(ip)
        return cls._instance

    def search_song_streamers(self, song_key: SongKey):
        return self._distributed_node.search_song_streamers(song_key)

    def store_song(self, song: SongDto):
        return self._distributed_node.store_song(song)

    def stream_song(self, song_key: SongKey, rang: tuple[int, int]):
        return self._distributed_node.stream_song(song_key, rang)

    def get_all_songs(self) -> list[SongDto]:
        return self._distributed_node.get_all_songs()

    def search_songs_by(self, search_by: str, query: str):
        return self._distributed_node.search_songs_by(search_by, query)
