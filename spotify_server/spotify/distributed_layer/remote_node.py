import socket
from enum import Enum

from .rpc_message import RpcRequest, RpcResponse
from .song_dto import SongDto


class RemoteFunctions(Enum):
    GET_KEYS_BY_QUERY = "get_keys_by_query"
    GET_NEARS_NODE = "get_nears_node"
    PING = "ping"
    SAVE_KEY = "save_key"
    GET_ALL_KEYS = "get_all_keys"


class RemoteNode:
    def __init__(self, ip: str, node_id: int):
        self.ip: str = ip
        self.id: int = node_id

    def save_key(self, node_ip: str, song: SongDto):
        try:
            with socket.socket() as sock:
                sock.bind((node_ip, 0))
                sock.settimeout(3)

                port = sock.getsockname()[1]
                request = RpcRequest(
                    (node_ip, port),
                    self.id,
                    RemoteFunctions.SAVE_KEY.value,
                    [song.to_dict()],
                )

                sock.connect((self.ip, 1729))
                sock.sendall(request.encode())

                data, _ = sock.recvfrom(1024)
                response: RpcResponse | None = RpcResponse.decode(data)
                if response:
                    return response.result
        except socket.timeout:
            pass

    def get_keys_by_query(self, node_ip: str, search_by: str, query: str):

        with socket.socket() as sock:
            sock.bind((node_ip, 0))
            sock.settimeout(3)

            port = sock.getsockname()[1]
            request = RpcRequest(
                (node_ip, port),
                self.id,
                RemoteFunctions.GET_KEYS_BY_QUERY.value,
                [query, search_by],
            )
            sock.connect((self.ip, 1729))
            sock.sendall(request.encode())

            try:
                data, _ = sock.recvfrom(1024)
                response: RpcResponse | None = RpcResponse.decode(data)
                if response:
                    return response.result
            except socket.timeout:
                pass

    def get_all_keys(self, node_ip: str):
        with socket.socket() as sock:
            sock.bind((node_ip, 0))
            sock.settimeout(3)

            port = sock.getsockname()[1]
            request = RpcRequest(
                (node_ip, port),
                self.id,
                RemoteFunctions.GET_ALL_KEYS.value,
                [],
            )
            sock.connect((self.ip, 1729))
            sock.sendall(request.encode())

            try:
                data, _ = sock.recvfrom(1024)
                response: RpcResponse | None = RpcResponse.decode(data)
                if response:
                    return response.result
            except socket.timeout:
                pass

    def get_nears_node(self, node_ip: str, target_id: int):
        try:
            with socket.socket() as sock:
                sock.bind((node_ip, 0))
                sock.settimeout(3)

                port = sock.getsockname()[1]
                request = RpcRequest(
                    (node_ip, port),
                    self.id,
                    RemoteFunctions.GET_NEARS_NODE.value,
                    [target_id],
                )
                sock.connect((self.ip, 1729))
                sock.sendall(request.encode())

                data, _ = sock.recvfrom(1024)
                response: RpcResponse | None = RpcResponse.decode(data)
                if response:
                    return response.result

                return None

        except socket.timeout:
            return None

    def ping(self) -> tuple[bool, str | None]:
        try:
            with socket.socket() as sock:
                sock.bind((self.ip, 0))
                sock.settimeout(3)

                port = sock.getsockname()[1]
                request = RpcRequest(
                    (self.ip, port),
                    self.id,
                    RemoteFunctions.PING.value,
                    [],
                )
                sock.connect((self.ip, 1729))
                sock.sendall(request.encode())

                data, _ = sock.recvfrom(1024)
                response: RpcResponse | None = RpcResponse.decode(data)
                if response:
                    return response.result

                return False, None

        except socket.timeout:
            return False, None

    def __eq__(self, other):
        return isinstance(other, RemoteNode) and self.id == other.id

    def __str__(self):
        return f"RemoteNode({self.ip}, with id: {self.id})"

    def __repr__(self):
        return str(self)
