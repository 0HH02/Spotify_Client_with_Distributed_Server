from .rpc_message import RpcRequest
from .utils import sha1_hash
from .network_interface import NetworkInterface
from .finger_table import FingerTable, K_BUCKET_SIZE

from ..services.song_services import SongServices
from ..models import SongKey


class KademliaNode:
    def __init__(self, ip: str):
        self.ip: str = ip
        self.id: int = sha1_hash(ip)
        self.network_interface = NetworkInterface(self)
        self.finger_table = FingerTable(self)

    def handle_request(self, request: RpcRequest, address: tuple[str, str]):
        pass

    def ping(self):
        pass

    def get_all_keys(self):
        pass

    def get_k_closest_nodes(self, key: int, k: int = K_BUCKET_SIZE):
        return self.finger_table.get_k_closets_nodes(key, k)

    def get_keys_by_query(self, query: str):
        pass

    def store_key(self, data: dict):
        pass

    def get_key(self, key: str):
        """ """
        song_key = SongKey.from_string(key)
        if self.constains_key(key):
            return SongServices.stream_song(song_key)

    def constains_key(self, key: str):
        song_key = SongKey.from_string(key)
        return SongServices.exists_song(song_key)
