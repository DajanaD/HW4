from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import urllib.parse
import mimetypes
import socket
from datetime import datetime
from threading import Thread
import logging
import json
from flask import Flask

BASE_DIR = Path()  
PORT_HTTP = 3000
HOST_HTTP = "0.0.0.0"
SOCKET_HOST = "127.0.0.1"
SOCKET_PORT = 5000
BUFFER_SIZE = 1024

class HttpHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        size = self.headers.get("Content-Length")
        data = self.rfile.read(int(size))
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))
        client_socket.close()
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    
    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case "/":
                self.send_html("index.html")
            case "/message":
                self.send_html("message.html")
            case _:
                file = BASE_DIR.joinpath(route.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html("error.html", 404)

    def send_html(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())
    
    def send_static(self, file):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

def save_data(data):
    data_parse = urllib.parse.unquote_plus(data.decode())
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        new_data = {current_time: {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}}

        file_path = "storage/data.json"

        try:
            with open(file_path, "r", encoding="utf-8") as file:  # спочатку читаєм та додаємо дані у словник
                existing_data = json.load(file)
        except FileNotFoundError: # Перевірка на файл
            existing_data = {}
        except ValueError: # Перевірка чи не пустий 
            existing_data = {}

        existing_data.update(new_data)

        with open(file_path, "w", encoding="utf-8") as file:  # повністю перезатираєм дані
            json.dump(existing_data, file, ensure_ascii=False, indent=2)

    except ValueError as error:
        logging.error(f"ValueError: {error}")
    except OSError as oser:
        logging.error(f"OSError: {oser}")

app = Flask(__name__)                       

@app.route('/')
def run_socket_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    logging.info("Starting socket")
    try:
        while True:
            msg, address = server_socket.recvfrom(BUFFER_SIZE)
            logging.info("++")
            save_data(msg)
    except KeyboardInterrupt:
        server_socket.close()


@app.route('/')
def run_http_server(host, port):
    address = (host, port)
    http_server = HTTPServer(address, HttpHandler)
    logging.info("Starting http")
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()
    app.run(debug=False, host='0.0.0.0')
            


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format="%(threadName)s%(message)s")

    ser_http = Thread(target=run_http_server, args=(HOST_HTTP, PORT_HTTP))
    ser_http.start()

    ser_socker = Thread(target=run_socket_server, args=(SOCKET_HOST, SOCKET_PORT))
    ser_socker.start()

    app.run(debug=False, host='0.0.0.0')