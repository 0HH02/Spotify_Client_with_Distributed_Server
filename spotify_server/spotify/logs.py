import threading

lock = threading.Lock()


def write_log(log: str) -> None:
    with lock:
        with open("./logs/logs.txt", "a") as f:
            f.write(log + "\n")
