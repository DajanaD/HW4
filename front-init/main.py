from http.server import HTTPServer, BaseHTTPRequestHandler
import pathlib
import urllib.parse
import mimetypes
import socket
from time import sleep
import threading
import datetime

class HttpHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        print(data)
        data_parse = urllib.parse.unquote_plus(data.decode())
        print(data_parse)
        data_dict = {key: datetime.now() for key, value in {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}}
        print(data_dict)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def echo_server(host, port):
        with socket.socket() as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            s.listen(1)
            conn, addr = s.accept()
            print(f"Connected by {addr}")
            with conn:
                while True:
                    data = conn.recv(1024)
                    print(f'From client: {data}')
                    if not data:
                        break
                    conn.send(data.upper())

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

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/contact':
            self.send_html_file('contact.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())
    
    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()

    HOST = '127.0.0.1'
    PORT = 5000

    server = threading.Thread(target=echo_server, args=(HOST, PORT))
    client = threading.Thread(target=simple_client, args=(HOST, PORT))

    server.start()
    client.start()
    server.join()
    client.join()
    print('Done!')

if __name__ == '__main__':
    run()

