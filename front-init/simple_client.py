import socket
from time import sleep

def simple_client(host, port):
        with socket.socket() as s:
            while True:
                try:
                    s.connect((host, port))
                    s.sendall(b'Hello, world')
                    data = s.recv(1024)
                    print(f'From server: {data}')
                    break
                except ConnectionRefusedError:
                    sleep(0.5)