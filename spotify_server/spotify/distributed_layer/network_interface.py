import socket
import ssl
import time
import threading
from concurrent.futures import ThreadPoolExecutor


from .rpc_message import RpcRequest, RpcResponse
from .remote_node import RemoteNode, RemoteFunctions
from .song_dto import SongDto


class NetworkInterface:
    def __init__(self, node):
        self.node = node
        self.listening: bool = False

    def _listen_new_nodes_request(self):
        print("listening to new nodes requests")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0", 1728))
            while self.listening:
                data, addr = sock.recvfrom(1024)
                node_id: str = data.decode()
                print(
                    f"node {node_id} with ip: {addr[0]} is requesting to join to the network"
                )
                bin_node_id = bin(int(node_id))
                if len(bin_node_id) == 160:
                    print("node_id is valid")
                    sender_id = str(self.node.id)
                    sock.sendto(sender_id.encode(), addr)
                    try:
                        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                        context.check_hostname = False
                        context.load_verify_locations(
                            "./spotify/distributed_layer/cert.pem",
                        )
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tsock:
                            with context.wrap_socket(tsock) as ssock:
                                ssock.settimeout(5)
                                ssock.connect((self.node.ip, 1729))
                                ssock.sendall(
                                    RpcRequest(
                                        node_id,
                                        RemoteFunctions.PING.value,
                                        [],
                                    ).encode()
                                )
                    except ConnectionRefusedError:
                        print("Node tcp server is not up")
                    except socket.timeout:
                        print("Timeout sending ping request to myself")
                else:
                    print("node_id is invalid")

    def _listen(self):
        print(f"starting listening in ip: {self.node.ip}")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(
            certfile="./spotify/distributed_layer/cert.pem",
            keyfile="./spotify/distributed_layer/key.pem",
        )

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listening_socket:
            listening_socket.bind(("0.0.0.0", 1729))
            listening_socket.listen(10)
            with context.wrap_socket(
                listening_socket, server_side=True
            ) as s_listening_socket:
                with ThreadPoolExecutor(5) as executor:
                    while self.listening:
                        conn, addr = s_listening_socket.accept()
                        executor.submit(self.handle_connection, conn, addr)

    def start_listening(self):
        self.listening = True
        threading.Thread(target=self._listen, args=[]).start()
        threading.Thread(target=self._listen_new_nodes_request, args=[]).start()

    def stop_listening(self):
        self.listening = False

    def discover_nodes(self) -> list[RemoteNode]:
        discovered_nodes: list[RemoteNode] = []
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.bind((self.node.ip, 0))
                message: str = str(self.node.id)

                print("requesting to joining the network")
                sock.sendto(message.encode(), ("255.255.255.255", 1728))
                print("sended broadcast")
                initial_time: float = time.time()
                while time.time() - initial_time < 5:
                    sock.settimeout(5)
                    print("waiting for nodes responses")
                    data, addr = sock.recvfrom(1024)
                    node_id: str = data.decode()
                    print(f"node {node_id} answer the join network request")
                    if len(node_id) == 160 and all(n in ["0", "1"] for n in node_id):
                        discovered_nodes.append(RemoteNode(addr[0], int(node_id)))

        except socket.timeout:
            print("Timeout sending discover broadcast")

        print("Ended discovering")
        return discovered_nodes

    def handle_connection(self, conn: socket.socket, addr: tuple[str, str]):
        try:
            data: bytes = conn.recv(1024)
            request: RpcRequest | None = RpcRequest.decode(data)
            if request:
                response: RpcResponse = self.handle_request(request, addr)
                conn.sendall(response.encode())
            else:
                pass
                # TODO enviar error al dueño del request
        finally:
            conn.close()

    def handle_request(self, request: RpcRequest, addr: tuple[str, str]) -> RpcResponse:
        request_node = RemoteNode(addr[0], request.sender_id)
        self.node.update_finger_table(request_node)

        print(f"Received request {request} from {request_node}")

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
