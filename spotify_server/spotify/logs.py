import threading

lock = threading.Lock()


def write_log(log: str, t=0) -> None:
    log_file = "c_logs.txt" if t == 0 else "k_logs.txt"
    with lock:
        with open(f"./logs/{log_file}", "a", encoding="utf-8") as f:
            f.write(log + "\n")
