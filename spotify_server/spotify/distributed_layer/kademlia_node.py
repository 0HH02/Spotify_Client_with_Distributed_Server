import threading
import time
from concurrent.futures import ThreadPoolExecutor
from heapq import heappush, heappop

from spotify.models import Song


from .remote_node import RemoteNode
from .utils import sha1_hash
from .network_interface import NetworkInterface
from .finger_table import FingerTable, K_BUCKET_SIZE
from .song_dto import SongDto, SongKey, SongMetadataDto

from ..services.song_services import SongServices
from ..logs import write_log

ALPHA = 3


class KademliaNode:
    def __init__(self, ip: str):
        self.ip: str = ip
        self.id: int = sha1_hash(ip)
        self.network_interface = NetworkInterface(self)
        self.finger_table = FingerTable(self)
        self.kademlia_interface = KademliaInterface(self)
        self.connected = False
        self.seeds: set[SongKey] = set()
        self.network_interface.start_listening()
        self._keep_kademlia_network_connection()
        self._ensure_persistance()

    def get_all_songs(self) -> tuple[list[SongMetadataDto], list[RemoteNode]]:
        write_log("Getting all songs", 4)
        nodes: list[RemoteNode] = self._search_all_nodes()
        songs: set[SongMetadataDto] = set()
        lock = threading.Lock()

        def _get_songs_from_node(node: RemoteNode):
            write_log(f"Getting songs from node {node}", 4)
            songs_from_node: list[SongMetadataDto] | None = node.get_all_keys(self.id)
            if songs_from_node:
                write_log(f"Got {len(songs_from_node)} songs from node {node}", 4)
                for song in songs_from_node:
                    write_log(f"Got song {song} from node {node}", 4)
                    with lock:
                        if song not in songs:
                            write_log(
                                f"Adding song {song} with hash {hash(song)} to songs", 4
                            )
                            songs.add(song)
                        else:
                            write_log(f"Song {song} already in songs", 4)

        with ThreadPoolExecutor(ALPHA) as executor:
            executor.map(_get_songs_from_node, nodes)

        # TODO improve this using hierarchy of nodes
        for song in self.kademlia_interface.get_all_songs():
            songs.add(SongMetadataDto.from_dict(song))

        write_log(f"Got {len(songs)} songs in total", 4)
        return list(songs), self.finger_table.get_active_nodes(K_BUCKET_SIZE)

    def search_songs_by(
        self, search_by: str, query: str
    ) -> tuple[list[SongMetadataDto], list[RemoteNode]]:
        nodes: list[RemoteNode] = self._search_all_nodes()
        songs: set[SongMetadataDto] = set()
        lock = threading.Lock()

        def _search_songs_by_from_node(node: RemoteNode):
            write_log(f"Searching songs from node {node}", 5)
            songs_from_node = node.get_keys_by_query(self.id, search_by, query)
            write_log(f"Got {len(songs_from_node)} songs from node {node}", 5)
            with lock:
                songs.update(songs_from_node)

        with ThreadPoolExecutor(ALPHA) as executor:
            executor.map(_search_songs_by_from_node, nodes)

        # TODO improve this using hierarchy of nodes
        for song in self.kademlia_interface.get_songs_by_query(search_by, query):
            songs.add(SongMetadataDto.from_dict(song))

        write_log(f"Got {len(songs)} songs in total", 5)
        return list(songs), self.finger_table.get_active_nodes(K_BUCKET_SIZE)

    def search_song_streamers(
        self, song_key: SongKey
    ) -> tuple[list[RemoteNode], list[RemoteNode]]:
        write_log(f"Searching song streamers, for key: {song_key}", 1)
        key: int = sha1_hash(str(song_key))
        nearest: list[RemoteNode] = self._search_k_nearest(key)

        # TODO improve this using hierarchy of nodes
        if len(nearest) < K_BUCKET_SIZE:
            nearest.append(RemoteNode(self.ip, self.id))
        elif nearest[-1].id ^ key > self.id ^ key:
            nearest.pop()
            nearest.append(RemoteNode(self.ip, self.id))

        return nearest, self.finger_table.get_active_nodes(K_BUCKET_SIZE)

    def store_song(self, song: SongDto) -> tuple[bool, list[RemoteNode]]:
        write_log(f"Storing song,{song}", 1)
        key: int = sha1_hash(str(song.key))
        nearest: list[RemoteNode] = self._search_k_nearest(key)
        write_log(f"The nearest nodes to song {song} are {nearest}", 1)

        local_save = True
        # TODO improve this using hierarchy of nodes
        if len(nearest) < K_BUCKET_SIZE:
            local_save = self.kademlia_interface.save_song(song, True)
            write_log("Saved song in local node and added to seeds", 6)
        elif nearest[-1].id ^ key > self.id ^ key:
            nearest.pop()
            local_save = self.kademlia_interface.save_song(song, True)
            write_log("Saved song in local node and added to seeds", 6)

        write_log(
            f"The distance between farest node and key is {nearest[-1].id ^ key} and the distance between self and key is {self.id ^ key}",
            1,
        )

        with ThreadPoolExecutor(ALPHA) as executor:
            results = executor.map(
                lambda node: node.save_key(self.id, song, node == nearest[0]), nearest
            )

        for n in results:
            write_log("Saved song in node" if n else "Failed to save song in node", 1)

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

    def _search_k_nearest(self, key: int, k: int = K_BUCKET_SIZE) -> list[RemoteNode]:
        write_log(f"Searching k nearest nodes to key {key}", 1)
        nearest: list[RemoteNode] = []
        pending: set[RemoteNode] = set()
        already_queried: set[RemoteNode] = set()
        lock = threading.Lock()

        for remote_node in self.finger_table.get_k_closets_nodes(key, k):
            heappush(nearest, (-(remote_node.id ^ key), remote_node))
            pending.add(remote_node)

        def _get_nears_node(_):
            with lock:
                current: RemoteNode = pending.pop()
                already_queried.add(current)
            new_nodes: list[RemoteNode] | None = current.get_nears_node(self.id, key)
            if new_nodes:
                for remote_node in new_nodes:
                    if remote_node.id == self.id:
                        continue
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

        result = [heappop(nearest)[1] for _ in range(min(k, len(nearest)))]
        write_log(f"The nearest nodes are {result}", 1)

        return result

    def _search_all_nodes(self):
        write_log("Searching all nodes", 4)
        nodes: list[RemoteNode] = []
        pendings: set[RemoteNode] = set()
        already_queried: set[RemoteNode] = set()
        lock = threading.Lock()

        for remote_node in self.finger_table.get_all_nodes():
            write_log(
                f"Adding node {remote_node} to pending nodes from finger table", 4
            )
            nodes.append(remote_node)
            pendings.add(remote_node)

        def _get_all_nodes_from_remote(_):
            write_log("Getting all nodes from remote", 4)
            with lock:
                current: RemoteNode = pendings.pop()
                write_log(f"Now gettings nodes from {current}", 4)
                already_queried.add(current)
            new_nodes = current.get_all_nodes()
            write_log(f"Got {len(new_nodes)} nodes from {current}", 4)
            if new_nodes:
                for remote_node in new_nodes:
                    if remote_node.id == self.id:
                        continue
                    with lock:
                        if (
                            remote_node not in already_queried
                            and remote_node not in pendings
                        ):
                            write_log(
                                f"Adding node {remote_node} to pending nodes from discovered nodes",
                                4,
                            )
                            nodes.append(remote_node)
                            pendings.add(remote_node)

        while pendings:
            with ThreadPoolExecutor(ALPHA) as executor:
                executor.map(_get_all_nodes_from_remote, range(ALPHA))

        write_log(f"Found {len(nodes)} nodes", 4)
        return nodes

    def _keep_connection_to_network(self):
        write_log("Starting to keep connection to network")
        while True:
            if len(self.finger_table.get_active_nodes(10)) < 3:
                discovered_nodes: list[RemoteNode] = (
                    self.network_interface.discover_nodes()
                )
                write_log(f"Discovered nodes {discovered_nodes}")
                if discovered_nodes:
                    for node in discovered_nodes:
                        self.finger_table.add_node(node)

                time.sleep(20)
                write_log("Waiting 20 seconds to discover new nodes")
            else:
                time.sleep(60)
                write_log("Waiting 60 seconds to discover new nodes")

    def _keep_kademlia_network_connection(self):
        threading.Thread(target=self._keep_connection_to_network, args=[]).start()

    def _ensure_persistance_service(self):
        write_log("Starting ensure persistance", 6)
        while True:
            for song in self.seeds:
                write_log(f"Verifiyng song {song} persistance in network", 6)
                key = sha1_hash(str(song))
                nearest = self._search_k_nearest(key)
                for node in nearest:
                    if node.constains_key(str(song), self.id):
                        write_log(f"Node {node} already constains song {song}", 6)
                        continue
                    song_data: Song | None = SongServices.get_song(song)
                    if not song_data:
                        write_log("Song is in seeds but is not in the database", 3)
                        self.seeds.remove(song)
                    else:
                        song_dto: SongDto | None = SongDto.from_dict(
                            song_data.to_dict()
                        )
                        if not song_dto:
                            write_log(
                                f"Error constructing song dto from song data for {song}",
                                6,
                            )
                        else:
                            node.save_key(self.id, song_dto)
                            write_log(f"Saved song {song_dto} in node {node}", 6)

            time.sleep(240)

    def _ensure_persistance(self):
        threading.Thread(target=self._ensure_persistance_service, args=[]).start()


class KademliaInterface:
    def __init__(self, node: KademliaNode):
        self.node: KademliaNode = node

    def ping(self) -> tuple[bool, int]:
        return True, self.node.id

    def get_all_songs(self) -> list[dict]:
        songs = SongServices.get_all_songs_metadata()
        write_log(f"Got {len(songs)} songs metadata from services", 4)
        metadata = [song.to_dict_metadata() for song in songs]
        for s in metadata:
            s["image"] = f"{self.node.ip}{s['image']}"
        return metadata

    def get_k_nearest(self, key: int, k: int = K_BUCKET_SIZE) -> list[RemoteNode]:
        return self.node.finger_table.get_k_closets_nodes(key, k)

    def get_songs_by_query(self, search_by: str, query: str) -> list[dict]:
        songs = SongServices.search_songs(search_by, query)
        metadata = [song.to_dict_metadata() for song in songs]
        for s in metadata:
            s["image"] = f"{self.node.ip}/{s['image']}"
        write_log(f"Se encontraron {len(metadata)} canciones", 5)
        return metadata

    def save_song(self, song: SongDto, seed: bool) -> bool:
        if SongServices.exists_song(song.key):
            write_log(f"Song {song} already exists", 6)
            return True
        uploaded = SongServices.upload_song(song)
        if uploaded:
            if seed:
                self.node.seeds.add(song.key)
            return True
        return False

    def constains_song(self, song_key: SongKey) -> bool:
        return SongServices.exists_song(song_key)

    def get_all_nodes(self) -> list[RemoteNode]:
        return self.node.finger_table.get_all_nodes()
