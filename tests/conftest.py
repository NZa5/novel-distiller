import socket
import pytest

@pytest.fixture(autouse=True)
def deny_network(monkeypatch, request):
    if request.node.get_closest_marker('live_api'):
        return
    def blocked(*args, **kwargs):
        raise AssertionError('network access is forbidden in Skill tests')
    monkeypatch.setattr(socket, 'create_connection', blocked)
    monkeypatch.setattr(socket.socket, 'connect', blocked)
