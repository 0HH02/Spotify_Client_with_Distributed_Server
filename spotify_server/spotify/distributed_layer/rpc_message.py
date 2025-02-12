import json
from abc import ABC, abstractmethod


class Encodable(ABC):

    @abstractmethod
    def encode(self) -> bytes:
        pass

    @staticmethod
    @abstractmethod
    def decode(data):
        pass


class RpcRequest(Encodable):
    def __init__(
        self, address: tuple[str, str], sender_id: int, function: str, arguments: list
    ):
        self.addres: tuple[str, str] = address
        self.sender_id: int = sender_id
        self.function: str = function
        self.arguments: str = arguments

    def encode(self) -> bytes:
        data = {
            "ip": self.addres[0],
            "id": self.sender_id,
            "port": self.addres[1],
            "function": self.function,
            "arguments": self.arguments,
        }
        return json.dumps(data).encode()

    @staticmethod
    def decode(data: bytes) -> "RpcRequest" | None:
        try:
            json_data = json.loads(data.decode())
            request = RpcRequest(
                address=(json_data["ip"], json_data["port"]),
                sender_id=json_data["sender_id"],
                function=json_data["function"],
                arguments=json_data["arguments"],
            )
            return request
        except (json.JSONDecodeError, KeyError):
            return None


class RpcResponse(Encodable):
    def __init__(self, result):
        self.result = result

    def encode(self) -> bytes:
        data = {"result": self.result}
        return json.dumps(data).encode()

    @staticmethod
    def decode(data: bytes) -> "RpcResponse" | None:
        try:
            json_data = json.loads(data.decode())
            response = RpcResponse(
                result=json_data["result"],
            )
            return response
        except (json.JSONDecodeError, KeyError):
            return None
