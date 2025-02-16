import socket
def listen():
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            ip = socket.gethostbyname(socket.gethostname())
            print(ip)
            sock.bind(("192.168.193.209", 1729))
            data, addr = sock.recvfrom(1024)
            print(data.decode())
listen()