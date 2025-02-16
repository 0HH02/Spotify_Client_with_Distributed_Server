import socket
import time
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor


from .rpc_message import RpcRequest, RpcResponse
from .remote_node import RemoteNode, RemoteFunctions
from .song_dto import SongDto


class NetworkInterface:
    def __init__(self, node):
        self.node = node
        self.listening: bool = False

    def _listen_new_nodes_request(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0", 1728))
            while self.listening:
                data, addr = sock.recvfrom(1024)
                node_id: str = data.decode()
                if len(node_id) == 160 and all(n in ["0", "1"] for n in node_id):
                    sock.sendto(self.node.id, addr)
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.connect((self.node.ip, 1729))
                        sock.sendall(
                            RpcRequest(
                                addr,
                                int(node_id),
                                RemoteFunctions.PING.value,
                                [],
                            )
                        )

    def _listen(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listening_socket:
            print(f"starting listening in ip: {self.node.ip}")
            listening_socket.bind((self.node.ip, 1729))
            listening_socket.listen(10)
            with ThreadPoolExecutor(5) as executor:
                while self.listening:
                    conn, addr = listening_socket.accept()
                    executor.submit(self.handle_connection, conn, addr)

    def start_listening(self):
        self.listening = True
        threading.Thread(target=self._listen, args=[]).start()
        multiprocessing.Process(target=self._listen_new_nodes_request, args=[]).start()

    def stop_listening(self):
        self.listening = False

    def discover_nodes(self) -> list[RemoteNode]:
        discovered_nodes: list[RemoteNode] = []
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.bind((self.node.ip, 0))
                message: str = str(self.node.id)

                sock.sendto(message.encode(), ("255.255.255.255", 1728))
                initial_time: float = time.time()
                while time.time() - initial_time < 5:
                    data, addr = sock.recvfrom(1024)
                    node_id: str = data.decode()
                    if len(node_id) == 160 and all(n in ["0", "1"] for n in node_id):
                        discovered_nodes.append(RemoteNode(addr[0], int(node_id)))

        except socket.timeout:
            print("Timeout sending discover broadcast")

        return discovered_nodes

    def handle_connection(self, conn: socket.socket, _: tuple[str, str]):
        try:
            data: bytes = conn.recv(1024)
            request: RpcRequest | None = RpcRequest.decode(data)
            if request:
                response: RpcResponse = self.handle_request(request)
                conn.sendall(response.encode())
            else:
                pass
                # TODO enviar error al dueño del request
        finally:
            conn.close()

    def handle_request(self, request: RpcRequest) -> RpcResponse:
        if request.function == RemoteFunctions.PING.value:
            return RpcResponse(self.node.kademlia_interface.ping())

        if request.function == RemoteFunctions.GET_NEARS_NODE.value:
            nears_nodes: list[RemoteNode] = self.node.kademlia_interface.get_k_nearest(
                request.arguments[0]
            )
            return RpcResponse([n.to_dict() for n in nears_nodes])

        if request.function == RemoteFunctions.GET_KEYS_BY_QUERY.value:
            return RpcResponse(
                self.node.kademlia_interface.get_songs_by_query(
                    request.arguments[0], request.arguments[1]
                )
            )

        if request.function == RemoteFunctions.SAVE_KEY.value:
            song_dto: SongDto | None = SongDto.from_dict(request.arguments[0])
            if song_dto:
                return RpcResponse(self.node.kademlia_interface.save_song(song_dto))

        if request.function == RemoteFunctions.GET_ALL_KEYS.value:
            return RpcResponse(self.node.kademlia_interface.get_all_metadata())

        if request.function == RemoteFunctions.GET_ALL_NODES.value:
            nodes = [n.to_dict() for n in self.node.kademlia_interface.get_all_nodes()]
            return RpcResponse(nodes)
