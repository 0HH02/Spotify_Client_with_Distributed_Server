import threading
import time
from concurrent.futures import ThreadPoolExecutor
from heapq import heappush, heappop


from .remote_node import RemoteNode
from .utils import sha1_hash
from .network_interface import NetworkInterface
from .finger_table import FingerTable, K_BUCKET_SIZE
from .song_dto import SongDto, SongKey, SongMetadataDto

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
        self.network_interface.start_listening()
        self._keep_kademlia_network_connection()

    def get_all_songs(self) -> tuple[list[SongMetadataDto], list[RemoteNode]]:
        nodes: list[RemoteNode] = self._search_all_nodes()
        songs: set[SongMetadataDto] = set()
        lock = threading.Lock()

        def _get_songs_from_node(node: RemoteNode):
            songs_from_node = node.get_all_keys()
            if songs_from_node:
                with lock:
                    songs.update(songs_from_node)

        with ThreadPoolExecutor(ALPHA) as executor:
            executor.map(_get_songs_from_node, nodes)

        # TODO improve this using hierarchy of nodes
        for song in self.kademlia_interface.get_all_metadata():
            print(song)
            songs.add(SongMetadataDto.from_dict(song))

        return list(songs), self.finger_table.get_active_nodes(K_BUCKET_SIZE)

    def search_songs_by(
        self, search_by: str, query: str
    ) -> tuple[list[SongMetadataDto], list[RemoteNode]]:
        nodes: list[RemoteNode] = self._search_all_nodes()
        songs: set[SongMetadataDto] = set()
        lock = threading.Lock()

        def _search_songs_by_from_node(node: RemoteNode):
            songs_from_node = node.get_keys_by_query(search_by, query)
            with lock:
                songs.update(songs_from_node)

        with ThreadPoolExecutor(ALPHA) as executor:
            executor.map(_search_songs_by_from_node, nodes)

        # TODO improve this using hierarchy of nodes
        for song in self.kademlia_interface.get_all_metadata():
            songs.add(SongMetadataDto.from_dict(song))

        return list(songs), self.finger_table.get_active_nodes(K_BUCKET_SIZE)

    def search_song_streamers(
        self, song_key: SongKey
    ) -> tuple[list[RemoteNode], list[RemoteNode]]:
        key: int = sha1_hash(str(song_key))
        nearest: list[RemoteNode] = self._search_k_nearest(key)

        # TODO improve this using hierarchy of nodes
        if len(nearest) < K_BUCKET_SIZE:
            nearest.append(RemoteNode(self.ip, self.id))
        elif nearest[-1].id ^ key > self.id ^ key:
            nearest.pop()
            nearest.append(RemoteNode(self.ip, self.id))

        return nearest, self.finger_table.get_all_nodes()

    def store_song(self, song: SongDto) -> tuple[bool, list[RemoteNode]]:
        key: int = sha1_hash(str(song.key))
        nearest: list[RemoteNode] = self._search_k_nearest(key)
        print(f"the nearest nodes to song {song} are {nearest}")

        local_save = True
        # TODO improve this using hierarchy of nodes
        if len(nearest) < K_BUCKET_SIZE:
            local_save = self.kademlia_interface.save_song(song)
        elif nearest[-1].id ^ key > self.id ^ key:
            nearest.pop()
            self.kademlia_interface.save_song(song)

        with ThreadPoolExecutor(ALPHA) as executor:
            results = executor.map(lambda node: node.save_key(song), nearest)

        for n in results:
            print("Saved song in node" if n else "Failed to save song in node")

        return local_save or any(results), self.finger_table.get_active_nodes(
            K_BUCKET_SIZE
        )

    def stream_song(self, key: SongKey, rang: tuple[int, int]):
        """ """
        if self._constains_song(key):
            return SongServices.stream_song(key, rang)

    def update_finger_table(self, node: RemoteNode):
        self.finger_table.add_node(node)

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
            new_nodes: list[RemoteNode] | None = current.get_nears_node(key)
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

        return [heappop(nearest)[1] for _ in range(min(k, len(nearest)))]

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
        print("Starting to keep connection to network")
        while True:
            if len(self.finger_table.get_active_nodes(10)) < 3:
                discovered_nodes: list[RemoteNode] = (
                    self.network_interface.discover_nodes()
                )
                print("Discovered nodes", discovered_nodes)
                if discovered_nodes:
                    for node in discovered_nodes:
                        self.finger_table.add_node(node)

                time.sleep(20)
                print("Waiting 20 seconds to discover new nodes")
            else:
                time.sleep(60)
                print("Waiting 60 seconds to discover new nodes")

    def _keep_kademlia_network_connection(self):
        threading.Thread(target=self._keep_connection_to_network, args=[]).start()


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
        if SongServices.exists_song(song.key):
            return True
        uploaded = SongServices.upload_song(song)
        if uploaded:
            return True
        return False

    def get_all_nodes(self) -> list[RemoteNode]:
        return self.node.finger_table.get_all_nodes()
