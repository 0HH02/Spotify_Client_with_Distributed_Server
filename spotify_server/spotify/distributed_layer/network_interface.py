import socket
import ssl
import time
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor


from .rpc_message import RpcRequest, RpcResponse
from .remote_node import RemoteNode, RemoteFunctions
from .song_dto import SongDto

from ..logs import write_log


class NetworkInterface:
    def __init__(self, node):
        self.node = node
        self.listening: bool = False

    def _listen_new_nodes_request(self):
        write_log("listening to new nodes requests")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0", 1728))
            while self.listening:
                data, addr = sock.recvfrom(1024)
                if addr[0] == self.node.ip:
                    continue
                mssg = data.decode()
                if mssg[0] == "1":
                    continue
                node_id: str = mssg[1:]
                write_log(
                    f"node {node_id} with ip: {addr[0]} is requesting to join to the network"
                )
                sender_id = str(self.node.id)
                sock.sendto(("1" + sender_id).encode(), addr)

    def _listen(self):
        write_log(
            f"starting listening in ip: {self.node.ip} node with id : {self.node.id}"
        )
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
                        write_log(f"Accepted conection from {addr}")
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
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_sock:
                udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                udp_sock.bind((self.node.ip, 0))
                message: str = "0" + str(self.node.id)

                write_log("requesting to joining the network")
                udp_sock.sendto(message.encode(), ("255.255.255.255", 1728))
                write_log("sended broadcast")
                initial_time: float = time.time()
                while time.time() - initial_time < 5:
                    udp_sock.settimeout(5)
                    write_log("waiting for nodes responses")
                    data, addr = udp_sock.recvfrom(1024)
                    mssg: str = data.decode()
                    if mssg[0] == "0":
                        continue
                    node_id: str = mssg[1:]
                    write_log(f"node {node_id} answer the join network request")
                    new_node = RemoteNode(addr[0], int(node_id))
                    discovered_nodes.append(new_node)

                    alive, _ = new_node.ping(self.node.id)
                    if alive:
                        write_log(f"Node {new_node} is alive and verified")

        except socket.timeout:
            write_log("Timeout sending discover broadcast")

        except ConnectionError:
            write_log("Error sending ping of confirmation")

        write_log("Ended discovering")
        return discovered_nodes

    def handle_connection(self, conn: socket.socket, addr: tuple[str, str]):
        write_log(f"Handling connection from {addr}")
        try:
            data: bytes = conn.recv(1024)
            request: RpcRequest | None = RpcRequest.decode(data)
            if request:
                write_log(f"Received request {request} from {addr}")
                response: RpcResponse = self.handle_request(request, addr)
                conn.sendall(response.encode())
            else:
                write_log("Invalid request received")
                # TODO enviar error al dueño del request
        finally:
            conn.close()

    def handle_request(self, request: RpcRequest, addr: tuple[str, str]) -> RpcResponse:
        request_node = RemoteNode(addr[0], request.sender_id)
        self.node.update_finger_table(request_node)

        write_log(f"Received request {request} from {request_node}")

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
