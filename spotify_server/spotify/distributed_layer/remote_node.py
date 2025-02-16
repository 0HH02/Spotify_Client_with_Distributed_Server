import socket
import time
from enum import Enum

from .rpc_message import RpcRequest, RpcResponse
from .song_dto import SongDto,SongMetadataDto


class RemoteFunctions(Enum):
    GET_KEYS_BY_QUERY = "get_keys_by_query"
    GET_NEARS_NODE = "get_nears_node"
    PING = "ping"
    SAVE_KEY = "save_key"
    GET_ALL_KEYS = "get_all_keys"
    GET_ALL_NODES = "get_nodes"


class RemoteNode:
    def __init__(self, ip: str, node_id: int):
        self.ip: str = ip
        self.id: int = node_id

    def save_key(self, node_ip: str, song: SongDto):
        tries: int = 0
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
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

                    data: bytes = sock.recv(1024)
                    response: RpcResponse | None = RpcResponse.decode(data)
                    if response:
                        return bool(response.result)
            except socket.timeout:
                print(f"Timeout making request{request} to {self.ip}")
                break
            except ConnectionError as error:
                print(error)
                if tries > 10:
                    break
                tries += 1
                time.sleep(0.2)

    def get_keys_by_query(
        self, node_ip: str, search_by: str, query: str
    ) -> list[SongMetadataDto] | None:
        tries: int = 0
        while True:
            try:
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

                    data: bytes = sock.recv(1024)
                    response: RpcResponse | None = RpcResponse.decode(data)
                    if response:
                        return [SongMetadataDto.from_dict(n) for n in response.result]

            except socket.timeout:
                print(f"Timeout making request{request} to {self.ip}")
                break
            except ConnectionError as e:
                print(e)
                if tries > 10:
                    break
                tries += 1
                time.sleep(0.2)

    def get_all_keys(self, node_ip: str) -> list[SongMetadataDto] | None:
        tries: int = 0
        while True:
            try:
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

                    data: bytes = sock.recv(1024)
                    response: RpcResponse | None = RpcResponse.decode(data)
                    if response:
                        return [SongMetadataDto.from_dict(n) for n in response]

            except socket.timeout:
                print(f"Timeout making request{request} to {self.ip}")
                break
            except ConnectionError as e:
                print(e)
                if tries > 10:
                    break
                tries += 1
                time.sleep(0.2)

    def get_nears_node(self, node_ip: str, target_id: int) -> list["RemoteNode"] | None:
        tries: int = 0
        while True:
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

                    data: bytes = sock.recv(1024)
                    response: RpcResponse | None = RpcResponse.decode(data)
                    if response:
                        return [RemoteNode.from_dict(n) for n in response.result]

                    return None

            except socket.timeout:
                print(f"Timeout making request{request} to {self.ip}")

            except ConnectionError as e:
                print(e)
                if tries > 10:
                    break
                tries += 1
                time.sleep(0.2)

    def ping(self) -> tuple[bool, str | None]:
        tries: int = 0
        while True:
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

                    data: bytes = sock.recv(1024)
                    response: RpcResponse | None = RpcResponse.decode(data)
                    if response:
                        return response.result[0], response.result[1]

                    return False, None

            except socket.timeout:
                print(f"Timeout making request{request} to {self.ip}")
                return False, None
            except ConnectionError as e:
                print(e)
                if tries > 10:
                    break
                tries += 1
                time.sleep(0.2)

    def get_all_nodes(self) -> list["RemoteNode"] | None:
        tries: int = 0
        while True:
            try:
                with socket.socket() as sock:
                    sock.bind((self.ip, 0))
                    sock.settimeout(3)

                    port = sock.getsockname()[1]
                    request = RpcRequest(
                        (self.ip, port),
                        self.id,
                        RemoteFunctions.GET_ALL_NODES,
                        [],
                    )

                    sock.connect((self.ip, 1729))
                    sock.sendall(request.encode())

                    data: bytes = sock.recv(1024)
                    response: RpcResponse | None = RpcResponse.decode(data)
                    if response:
                        return [RemoteNode.from_dict(n) for n in response.result]

                    return []
            except socket.timeout:
                print(f"Timeout making request{request} to {self.ip}")
                return []
            except ConnectionError as e:
                print(e)
                if tries > 10:
                    break
                tries += 1
                time.sleep(0.2)

    def __eq__(self, other):
        return isinstance(other, RemoteNode) and self.id == other.id

    def to_dict(self):
        return {
            "id": self.id,
            "ip": self.ip,
        }

    @staticmethod
    def from_dict(dct: dict):
        return RemoteNode(dct["ip"], dct["id"])

    def __str__(self):
        return f"RemoteNode({self.ip}, with id: {self.id})"

    def __repr__(self):
        return str(self)
