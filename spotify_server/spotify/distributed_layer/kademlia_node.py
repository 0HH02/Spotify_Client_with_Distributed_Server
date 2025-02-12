import threading
from concurrent.futures import ThreadPoolExecutor
from heapq import heappush, heappop


from spotify.distributed_layer.remote_node import RemoteNode

from .utils import sha1_hash
from .network_interface import NetworkInterface
from .finger_table import FingerTable, K_BUCKET_SIZE
from .song_dto import SongDto, SongKey

from ..services.song_services import SongServices

ALPHA = 5


class KademliaNode:
    def __init__(self, ip: str):
        self.ip: str = ip
        self.id: int = sha1_hash(ip)
        self.network_interface = NetworkInterface(self)
        self.finger_table = FingerTable(self)
        self.kademlia_interface = KademliaInterface(self)
        self.connected = False

    def search_song(self, song_key: SongKey):
        key: int = sha1_hash(str(song_key))
        nearest: list[RemoteNode] = self._search_k_nearest(key)

        return nearest

    def store_song(self, song: SongDto):
        key: int = sha1_hash(str(song.key))
        nearest: list[RemoteNode] = self._search_k_nearest(key)

        with ThreadPoolExecutor(ALPHA) as executor:
            results = executor.map(lambda node: node.save_key(song), nearest)

        if all(results):
            return True

    def stream_song(self, key: SongKey):
        """ """
        if self.constains_song(key):
            return SongServices.stream_song(key)

    def constains_song(self, key: SongKey):
        return SongServices.exists_song(key)

    def _search_k_nearest(self, key: int, k: int = K_BUCKET_SIZE):
        nearest: list[RemoteNode] = []
        pending: set[RemoteNode] = set()
        already_queried: set[RemoteNode] = set()
        lock = threading.Lock()

        for remote_node in self.finger_table.get_k_closets_nodes(key, k):
            heappush(nearest, (-(remote_node.id ^ key), remote_node))
            pending.add(remote_node)

        def _get_nears_node():
            with lock:
                current: RemoteNode = pending.pop()
                already_queried.add(current)
            new_nodes: list[RemoteNode] | None = current.get_nears_node(self.ip, key)
            if new_nodes:
                for remote_node in new_nodes:
                    with lock:
                        if remote_node not in already_queried:
                            heappush(nearest, (-(remote_node.id ^ key), remote_node))
                            pending.add(remote_node)

        while pending:
            with ThreadPoolExecutor(ALPHA) as executor:
                executor.map(_get_nears_node, range(ALPHA))

        return [heappop(nearest)[1] for _ in range(k)]


class KademliaInterface:
    def __init__(self, node: KademliaNode):
        self.node: KademliaNode = node

    def ping(self) -> tuple[bool, int]:
        return True, self.node.id

    def get_all_metadata(self) -> list[dict]:
        songs = SongServices.get_all_songs_metadata()
        return [song.to_dict_metadata() for song in songs]

    def get_k_nearest(self, key: int, k: int = K_BUCKET_SIZE) -> list:
        return self.node.finger_table.get_k_closets_nodes(key, k)

    def get_songs_by_query(self, search_by: str, query: str) -> list[dict]:
        songs = SongServices.search_songs(search_by, query)
        return [song.to_dict_metadata() for song in songs]

    def save_song(self, song: SongDto) -> bool:
        uploaded = SongServices.upload_song(song)
        if uploaded:
            return True
        return False
