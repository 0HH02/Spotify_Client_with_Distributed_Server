import threading

lock = threading.Lock()


def write_log(log: str, t=0) -> None:

    logs = {
        0: "c_logs.txt",
        1: "s_logs.txt",
        2: "v_logs.txt",
        3: "e_logs.txt",
        4: "g_logs.txt",
        5: "q_logs.txt",
        6: "r_logs.txt",
    }
    log_file = logs[t]
    with lock:
        with open(f"./logs/{log_file}", "a", encoding="utf-8") as f:
            f.write(log + "\n")
