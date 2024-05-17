from typing import Any

import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.tcpserver
import tornado.gen
import socket

from tornado import httputil


class IRCWebSocketHandler(tornado.websocket.WebSocketHandler):
    clients = {}

    def __init__(
            self,
            application: tornado.web.Application,
            request: httputil.HTTPServerRequest,
            **kwargs: Any
    ):
        super().__init__(application, request)
        self.nickname = None

    def open(self):
        self.stream.set_nodelay(True)
        print("WebSocket opened.")
        IRCWebSocketHandler.clients[self] = None

    def on_message(self, message):
        if not hasattr(self, 'nickname'):  # Check if nickname is set
            self.nickname = message.strip()  # Set the nickname
            IRCWebSocketHandler.clients[self] = self.nickname
            self.write_message(f"Nickname set to {self.nickname}")
        else:
            print(f"Received message from {self.nickname}: {message}")
            for client, nickname in IRCWebSocketHandler.clients.items():
                if client != self:
                    client.write_message(f"{nickname}: {message}")

    def on_close(self):
        if self in IRCWebSocketHandler.clients:
            del IRCWebSocketHandler.clients[self]
        print("WebSocket closed.")


class TCPServer(tornado.tcpserver.TCPServer):
    async def handle_stream(self, stream, address):
        print(f"New connection from {address}")
        while True:
            try:
                data = await stream.read_until(b'\n')
                message = data.strip().decode()
                print(f"Received message: {message}")
                for client, nickname in IRCWebSocketHandler.clients.items():
                    await client.write_message(f"TCP: {message}")
            except (tornado.iostream.StreamClosedError, socket.error):
                print(f"Connection closed by {address}")
                break


def make_app():
    return tornado.web.Application([
        (r"/websocket", IRCWebSocketHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    server = TCPServer()
    server.listen(6667)
    print("IRC Server running on WebSocket port 8888 and TCP port 6667")
    tornado.ioloop.IOLoop.current().start()
