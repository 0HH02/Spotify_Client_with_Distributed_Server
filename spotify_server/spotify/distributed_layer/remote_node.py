import socket
import ssl
import time
from hashlib import sha256
from enum import Enum

from .rpc_message import RpcRequest, RpcResponse
from .song_dto import SongDto, SongMetadataDto
from ..logs import write_log


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

    def save_key(self, sender_id: int, song: SongDto):
        tries: int = 0
        while True:
            try:
                write_log("Trying to save key", 2)
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                context.check_hostname = False
                context.load_verify_locations("./spotify/distributed_layer/cert.pem")
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    with context.wrap_socket(sock, server_hostname=self.ip) as ssock:
                        ssock.settimeout(6)

                        port = ssock.getsockname()[1]
                        request = RpcRequest(
                            sender_id,
                            RemoteFunctions.SAVE_KEY.value,
                            [
                                song.to_dict(),
                                sha256(song.image.image_data).hexdigest(),
                                sha256(song.audio_data).hexdigest(),
                            ],
                        )
                        write_log(f"Enconding request {request}", 1)
                        ssock.connect((self.ip, 1729))
                        write_log(f"Connected to remote node {self}", 1)
                        ssock.sendall(request.encode())
                        write_log("Sended request", 1)
                        response = ssock.recv(8192)
                        if response.decode() == "Ok":
                            ssock.sendall(song.image.image_data)
                            write_log(
                                f"Imagen enviada con {len(song.image.image_data)} bytes y hash {sha256(song.image.image_data).hexdigest()}",
                                1,
                            )
                            response_image: bytes = ssock.recv(8192)
                            if response_image.decode() == "Img Ok":
                                write_log("Confirmacion de envio de imagen recibida", 1)
                                ssock.sendall(song.audio_data)
                            else:
                                write_log("Error enviando imagen", 1)
                                break
                        else:
                            write_log("Error enviando cancion", 1)
                            break

                        write_log("Cancion enviada", 1)
                        data: bytes = ssock.recv(8192)
                        response: RpcResponse | None = RpcResponse.decode(data)
                        write_log(
                            f"Received response {response} to request save_key", 1
                        )
                        if response:
                            return bool(response.result)

            except socket.timeout:
                write_log(f"Timeout making request {request} to {self}", 3)
                tries += 1
                time.sleep(0.2)
            except ConnectionError as error:
                write_log(f"Connection error making {request} to {self} : {error}", 3)
                tries += 1
                time.sleep(0.2)
            except Exception as e:
                tries += 1
                time.sleep(0.2)
                write_log(f"Exception ocurred making {request} to {self} : {e}", 3)

            if tries > 2:
                break

    def get_keys_by_query(
        self, sender_id, search_by: str, query: str
    ) -> list[SongMetadataDto] | None:
        tries: int = 0
        while True:
            try:
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                context.check_hostname = False
                context.load_verify_locations("./spotify/distributed_layer/cert.pem")
                with socket.socket() as sock:
                    with context.wrap_socket(sock, server_hostname=self.ip) as ssock:
                        ssock.settimeout(3)

                        port = ssock.getsockname()[1]
                        request = RpcRequest(
                            sender_id,
                            RemoteFunctions.GET_KEYS_BY_QUERY.value,
                            [search_by, query],
                        )
                        ssock.connect((self.ip, 1729))
                        write_log(
                            f"Connecting to ip: {self.ip} from address{port} sending request {request}",
                            5,
                        )
                        ssock.sendall(request.encode())

                        data: bytes = ssock.recv(8192)
                        response: RpcResponse | None = RpcResponse.decode(data)
                        write_log(f"Received response {response} to request", 5)
                        if response:
                            return [
                                SongMetadataDto.from_dict(n) for n in response.result
                            ]

            except socket.timeout:
                write_log(f"Timeout making request{request} to {self.ip}", 3)
                tries += 1
                time.sleep(0.2)
            except ConnectionError as e:
                write_log(
                    f"Connection error making request {request} to {self}: {e}", 3
                )
                tries += 1
                time.sleep(0.2)
            except Exception as e:
                write_log(f"Exception ocurred making {request} to {self} : {e}", 3)
                tries += 1
                time.sleep(0.2)

            if tries > 2:
                break

    def get_all_keys(self, sender_id: int) -> list[SongMetadataDto] | None:
        tries: int = 0
        while True:
            try:
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                context.check_hostname = False
                context.load_verify_locations("./spotify/distributed_layer/cert.pem")
                with socket.socket() as sock:
                    with context.wrap_socket(sock, server_hostname=self.ip) as ssock:

                        ssock.settimeout(3)
                        port = ssock.getsockname()[1]
                        request = RpcRequest(
                            sender_id,
                            RemoteFunctions.GET_ALL_KEYS.value,
                            [],
                        )
                        ssock.connect((self.ip, 1729))
                        write_log(
                            f"Trying to connect to ip: {self.ip} from address{port} sending request {request}",
                            4,
                        )
                        ssock.sendall(request.encode())
                        write_log("Sended request get all keys", 4)

                        data: bytes = ssock.recv(8192)
                        write_log(f"Received data {data}", 4)
                        response: RpcResponse | None = RpcResponse.decode(data)
                        write_log(f"Received response {response} to request", 4)
                        if response:
                            return [
                                SongMetadataDto.from_dict(n) for n in response.result
                            ]

            except socket.timeout:
                write_log(f"Timeout making request{request} to {self.ip}", 3)
                break
            except ConnectionError as e:
                write_log(e, 3)
                if tries > 10:
                    break
                tries += 1
                time.sleep(0.2)

    def get_nears_node(
        self, sender_id: int, target_id: int
    ) -> list["RemoteNode"] | None:
        tries: int = 0
        while True:
            try:
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                context.check_hostname = False
                context.load_verify_locations("./spotify/distributed_layer/cert.pem")
                with socket.socket() as sock:
                    with context.wrap_socket(sock, server_hostname=self.ip) as ssock:

                        ssock.settimeout(3)
                        port = ssock.getsockname()[1]
                        request = RpcRequest(
                            sender_id,
                            RemoteFunctions.GET_NEARS_NODE.value,
                            [target_id],
                        )
                        ssock.connect((self.ip, 1729))
                        write_log(
                            f"Trying to connect to ip: {self.ip} from address{port} sending request {request}"
                        )
                        ssock.sendall(request.encode())

                        data: bytes = ssock.recv(8192)
                        response: RpcResponse | None = RpcResponse.decode(data)
                        write_log(f"Received response {response} to request")
                        if response:
                            return [RemoteNode.from_dict(n) for n in response.result]

                        return None

            except socket.timeout:
                write_log(f"Timeout making request{request} to {self.ip}")

            except ConnectionError as e:
                write_log(e)
                if tries > 10:
                    break
                tries += 1
                time.sleep(0.2)

    def ping(self, sender_id: int) -> tuple[bool, str | None]:
        tries: int = 0
        while True:
            try:
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                context.check_hostname = False
                context.load_verify_locations("./spotify/distributed_layer/cert.pem")
                with socket.socket() as sock:
                    with context.wrap_socket(sock, server_hostname=self.ip) as ssock:

                        ssock.settimeout(3)
                        port = ssock.getsockname()[1]
                        request = RpcRequest(
                            sender_id,
                            RemoteFunctions.PING.value,
                            [],
                        )
                        ssock.connect((self.ip, 1729))
                        write_log(
                            f"Trying to connect to ip: {self.ip} from address{port} sending request {request}"
                        )
                        ssock.sendall(request.encode())

                        data: bytes = ssock.recv(8192)
                        response: RpcResponse | None = RpcResponse.decode(data)
                        write_log(f"Received response {response} to request")
                        if response:
                            return response.result[0], response.result[1]

                        return False, None

            except socket.timeout:
                write_log(f"Timeout making request{request} to {self.ip}")
                return False, None
            except ConnectionError as e:
                write_log(e)
                if tries > 10:
                    break
                tries += 1
                time.sleep(0.2)

    def get_all_nodes(self) -> list["RemoteNode"] | None:
        tries: int = 0
        while True:
            try:
                context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                context.check_hostname = False
                context.load_verify_locations("./spotify/distributed_layer/cert.pem")
                with socket.socket() as sock:
                    with context.wrap_socket(sock, server_hostname=self.ip) as ssock:

                        ssock.settimeout(3)
                        port = ssock.getsockname()[1]
                        request = RpcRequest(
                            self.id,
                            RemoteFunctions.GET_ALL_NODES,
                            [],
                        )

                        ssock.connect((self.ip, 1729))
                        write_log(
                            f"Trying to connect to ip: {self.ip} from address{port} sending request {request}"
                        )
                        ssock.sendall(request.encode())

                        data: bytes = ssock.recv(8192)
                        response: RpcResponse | None = RpcResponse.decode(data)
                        write_log(f"Received response {response} to request")
                        if response:
                            return [RemoteNode.from_dict(n) for n in response.result]

                        return []
            except socket.timeout:
                write_log(f"Timeout making request{request} to {self.ip}")
                return []
            except ConnectionError as e:
                write_log(e)
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

    def __hash__(self) -> int:
        return self.id.__hash__()

    def __str__(self) -> str:
        return f"RemoteNode({self.ip}, with id: {self.id})"

    def __repr__(self) -> str:
        return str(self)
