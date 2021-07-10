from twisted.internet import reactor
from main import slskFactory
from db import get_port


def run_server(port):
    """Runs the server"""
    reactor.listenTCP(port, slskFactory())
    reactor.run()


if __name__ == "__main__":
    port = get_ports()
    run_server(port)
