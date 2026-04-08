from twisted.trial import unittest
from twisted.internet.defer import inlineCallbacks
from twisted.internet.address import IPv4Address
from ..server_websocket import WebSocketServerFactory
from autobahn.twisted.testing import create_pumper, create_memory_agent, MemoryReactorClockResolver
from autobahn.twisted.websocket import WebSocketClientProtocol


class FakeServer:
    """
    Fake enough of the internal 'Server' object to appease the
    WebSocket server.

    """
    def get_welcome(self):
        return {
            "motd": "fake message of the day"
        }

    def get_log_requests(self):
        return False


class WebSocket(unittest.TestCase):
    """
    Details of the server WebSocket protocol
    """

    def setUp(self):
        self.pumper = create_pumper()
        self.reactor = MemoryReactorClockResolver()
        return self.pumper.start()

    def tearDown(self):
        return self.pumper.stop()

    def create_server_protocol(self):
        """
        Used by the Agent to create the in-memory transport server-side
        WebSocket protocol (we actually create the 'real' protocol
        objects since that is what we're testing here.)
        """
        factory = WebSocketServerFactory(
            "ws://localhost:4000/v1",
            FakeServer(),
        )
        addr = IPv4Address("TCP", "localhost", 4000)
        return factory.buildProtocol(addr)

    @inlineCallbacks
    def test_server_version_string(self):
        """
        Our server version string from Autobahn should make sense
        """
        server_header = None
        agent = create_memory_agent(
            self.reactor,
            self.pumper,
            self.create_server_protocol
        )
        
        class FakeClient(WebSocketClientProtocol):
            def onConnect(self, cr):
                nonlocal server_header
                server_header = cr.headers.get("server")
        
        proto = yield agent.open("ws://localhost:4000/v1", dict(), FakeClient)
        proto.sendClose()
        yield proto.is_closed

        assert "Magic Wormhole" in server_header, "Incorrect Server: header sent"
