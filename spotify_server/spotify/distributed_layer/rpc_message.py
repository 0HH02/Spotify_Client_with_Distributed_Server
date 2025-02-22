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
    def __init__(self, sender_id: int, function: str, arguments: list):
        self.sender_id: int = sender_id
        self.function: str = function
        self.arguments: str = arguments

    def encode(self) -> bytes:
        data = {
            "id": self.sender_id,
            "function": self.function,
            "arguments": self.arguments,
        }
        return json.dumps(data).encode()

    @staticmethod
    def decode(data: bytes):
        try:
            json_data = json.loads(data.decode())
            request = RpcRequest(
                sender_id=json_data["sender_id"],
                function=json_data["function"],
                arguments=json_data["arguments"],
            )
            return request
        except (json.JSONDecodeError, KeyError):
            return None

    def __str__(self) -> str:
        return f"Function: {self.function} with arguments: {self.arguments}"

    def __repr__(self) -> str:
        return self.__str__()


class RpcResponse(Encodable):
    def __init__(self, result):
        self.result = result

    def encode(self) -> bytes:
        data = {"result": self.result}
        return json.dumps(data).encode()

    @staticmethod
    def decode(data: bytes):
        try:
            json_data = json.loads(data.decode())
            response = RpcResponse(
                result=json_data["result"],
            )
            return response
        except (json.JSONDecodeError, KeyError):
            return None
