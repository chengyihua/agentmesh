import pytest
import asyncio
from fastapi.testclient import TestClient
from agentmesh.api.server import create_server
from agentmesh.client import AgentMeshClient

@pytest.fixture(scope="session")
def api_client():
    server = create_server(storage="memory", debug=True)
    with TestClient(server.app) as client:
        yield client

@pytest.fixture(scope="session")
def mesh_client():
    # Configure client to point to TestClient or local server
    client = AgentMeshClient(base_url="http://testserver")
    return client
