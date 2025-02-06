import socket
import threading

from .rpc_message import RpcRequest, RpcResponse

from .kademlia_node import KademliaNode
from .remote_node import RemoteNode, RemoteFunctions


class NetworkInterface:
    def __init__(self, node: KademliaNode):
        self.node: KademliaNode = node
        self.listening: bool = False

    def send_response(self, response, address: tuple[str, str]):
        with socket.socket() as sock:
            sock.settimeout(3)
            sock.connect(address)
            sock.sendall(RpcResponse(response).encode())

    def _listen(self):
        with socket.socket() as listening_socket:
            print(f"starting listening in ip: {self.node.ip}")
            listening_socket.bind((self.node.ip, 1729))
            while self.listening:
                data, addr = listening_socket.recvfrom(1024)
                request: RpcRequest | None = RpcRequest.decode(data)
                if request:
                    threading.Thread(
                        target=self.handle_request, args=[request, addr]
                    ).start()
                else:
                    print("Invalid Request")
                    # ask for best behavior in this case

    def start_listening(self):
        self.listening = True
        threading.Thread(target=self._listen, args=[]).start()

    def stop_listening(self):
        self.listening = False

    def discover_nodes(self):
        discovered_nodes = []
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(3)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind((self.node.ip, 0))
            port = sock.getsockname()[1]
            message = RpcRequest(
                (self.node.ip, port),
                RemoteFunctions.PING.value,
                [],
            )

            sock.sendto(message.encode(), ("255.255.255.255", 1729))

            try:
                while True:
                    data, addr = sock.recvfrom(1024)
                    response: RpcResponse | None = RpcResponse.decode(data)
                    if response:
                        discovered_nodes.append(RemoteNode(addr[0], response.result))
            except socket.timeout:
                pass

        return discovered_nodes

    def handle_request(self, request: RpcRequest, address: tuple[str, str]):
        if request.function == RemoteFunctions.PING.value:
            self.send_response(True, address)
        elif request.function == RemoteFunctions.GET_NEARS_NODE.value:
            self.send_response(
                self.node.get_k_closest_nodes(request.arguments[0]), address
            )
        elif request.function == RemoteFunctions.GET_KEYS_BY_QUERY.value:
            self.send_response(
                self.node.get_keys_by_query(request.arguments[0]),
                address,
            )
