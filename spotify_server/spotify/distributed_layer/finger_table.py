from heapq import heappop, heappush
from concurrent.futures import ThreadPoolExecutor
from .remote_node import RemoteNode

K_BUCKET_SIZE = 4


class KBucket:
    def __init__(self, k: int = K_BUCKET_SIZE) -> None:
        self.k: int = k
        self._nodes: set[RemoteNode] = set()
        self._failures: set[RemoteNode] = set()

    def add_node(self, node: RemoteNode) -> None:
        if len(self._nodes) < self.k:
            self._nodes.add(node)
        else:
            with ThreadPoolExecutor(3) as executor:
                executor.map(self.check_node, self._nodes)

            if len(self._failures) > 0:
                self._nodes.remove(self._failures.pop())
                self._nodes.add(node)
                self._failures.clear()

    def check_node(self, node: RemoteNode) -> None:
        aviable: bool = node.ping()
        if not aviable:
            self._failures.add(node)

    @property
    def nodes(self) -> list[RemoteNode]:
        return list(self._nodes)


class FingerTable:
    def __init__(self, node):
        self.buckets: list[KBucket] = [KBucket() for _ in range(160)]
        self.node = node

    def get_all_nodes(self) -> list[RemoteNode]:
        return [node for bucket in self.buckets for node in bucket.nodes]

    def get_k_closets_nodes(self, key: int, k: int) -> list[RemoteNode]:
        closest_nodes: list[RemoteNode] = []
        distance_bit: int = self.get_bit_distance(key)

        for remote_node in self.buckets[distance_bit].nodes:
            heappush(closest_nodes, (-(remote_node.id ^ key), remote_node))

        next_k_bucket: int = distance_bit + 1
        previous_k_bucket: int = distance_bit - 1
        still_searching: bool = True
        while len(closest_nodes) < k and still_searching:
            still_searching = False
            if next_k_bucket < len(self.buckets):
                for remote_node in self.buckets[next_k_bucket].nodes:
                    heappush(closest_nodes, (-(remote_node.id ^ key), remote_node))

                next_k_bucket += 1
                still_searching = True

            if previous_k_bucket > 0:
                for remote_node in self.buckets[previous_k_bucket].nodes:
                    heappush(closest_nodes, (-(remote_node.id ^ key), remote_node))

                previous_k_bucket -= 1
                still_searching = True

        return [heappop(closest_nodes)[1] for _ in range(min(k, len(closest_nodes)))]
    def add_node(self, remote_node: RemoteNode):
        distance_bit: int = self.get_bit_distance(remote_node.id)
        self.buckets[distance_bit].add_node(remote_node)

    def get_bit_distance(self, key: int) -> int:
        distance: int = key ^ self.node.id
        return distance.bit_length()
