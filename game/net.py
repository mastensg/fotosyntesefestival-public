import socket

class Display:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def __call__(self, message):
        self.socket.sendto(message + "\n", ("127.0.0.1", 9930))
