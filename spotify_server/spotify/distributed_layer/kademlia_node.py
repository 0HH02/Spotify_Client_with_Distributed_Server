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
        threading.Thread(target=self._keep_connection_to_network, args=[]).start()

    def get_all_songs(self) -> list[SongDto]:
        nodes: list[RemoteNode] = self._search_all_nodes()
        songs: set[SongDto] = set()
        lock = threading.Lock()

        def _get_songs_from_node(node: RemoteNode):
            songs_from_node = node.get_all_keys(self.ip)
            with lock:
                songs.update(songs_from_node)

        with ThreadPoolExecutor(ALPHA) as executor:
            executor.map(_get_songs_from_node, nodes)

        for song in self.kademlia_interface.get_all_metadata():
            songs.add(SongDto.from_dict(song))

        return list(songs)

    def search_songs_by(self, search_by: str, query: str):
        nodes: list[RemoteNode] = self._search_all_nodes()
        songs: set[SongDto] = set()
        lock = threading.Lock()

        def _search_songs_by_from_node(node: RemoteNode):
            songs_from_node = node.get_keys_by_query(self.ip, search_by, query)
            with lock:
                songs.update(songs_from_node)

        with ThreadPoolExecutor(ALPHA) as executor:
            executor.map(_search_songs_by_from_node, nodes)

        for song in self.kademlia_interface.get_all_metadata():
            songs.add(SongDto.from_dict(song))

        return list(songs)

    def search_song_streamers(self, song_key: SongKey):
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

    def stream_song(self, key: SongKey, rang: tuple[int, int]):
        """ """
        if self._constains_song(key):
            return SongServices.stream_song(key, rang)

    def _constains_song(self, key: SongKey):
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
                        if (
                            remote_node not in already_queried
                            and remote_node not in pending
                        ):
                            heappush(nearest, (-(remote_node.id ^ key), remote_node))
                            pending.add(remote_node)

        while pending:
            with ThreadPoolExecutor(ALPHA) as executor:
                executor.map(_get_nears_node, range(ALPHA))

        return [heappop(nearest)[1] for _ in range(k)]

    def _search_all_nodes(self):
        nodes: list[RemoteNode] = []
        pendings: set[RemoteNode] = set()
        already_queried: set[RemoteNode] = set()
        lock = threading.Lock()

        for remote_node in self.finger_table.get_all_nodes():
            nodes.append(remote_node)
            pendings.add(remote_node)

        def _get_all_nodes_from_remote():
            with lock:
                current: RemoteNode = pendings.pop()
                already_queried.add(current)
            new_nodes = current.get_all_nodes()
            if new_nodes:
                for remote_node in new_nodes:
                    with lock:
                        if (
                            remote_node not in already_queried
                            and remote_node not in pendings
                        ):
                            nodes.append(remote_node)
                            pendings.add(remote_node)

        while pendings:
            with ThreadPoolExecutor(ALPHA) as executor:
                executor.map(_get_all_nodes_from_remote, range(ALPHA))

        return nodes

    def _keep_connection_to_network(self):
        while True:
            discovered_nodes: list[RemoteNode] = self.network_interface.discover_nodes()
            if discovered_nodes:
                for node in discovered_nodes:
                    self.finger_table.add_node(node)
                break


class KademliaInterface:
    def __init__(self, node: KademliaNode):
        self.node: KademliaNode = node

    def ping(self) -> tuple[bool, int]:
        return True, self.node.id

    def get_all_metadata(self) -> list[dict]:
        songs = SongServices.get_all_songs_metadata()
        return [song.to_dict_metadata() for song in songs]

    def get_k_nearest(self, key: int, k: int = K_BUCKET_SIZE) -> list[RemoteNode]:
        return self.node.finger_table.get_k_closets_nodes(key, k)

    def get_songs_by_query(self, search_by: str, query: str) -> list[dict]:
        songs = SongServices.search_songs(search_by, query)
        return [song.to_dict_metadata() for song in songs]

    def save_song(self, song: SongDto) -> bool:
        uploaded = SongServices.upload_song(song)
        if uploaded:
            return True
        return False

    def get_all_nodes(self) -> list[RemoteNode]:
        return self.node.finger_table.get_all_nodes()
