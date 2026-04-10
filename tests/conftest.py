"""
Pytest fixtures for TechDetector tests.
"""
import pytest
import asyncio
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer


@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def postgres():
    """Spin up a PostgreSQL testcontainer for integration tests."""
    with PostgresContainer("postgres:15") as pg:
        yield pg.get_connection_url().replace("+psycopg2", "")


@pytest.fixture(scope="session")
def redis():
    """Spin up a Redis testcontainer for integration tests."""
    with RedisContainer("redis:7-alpine") as r:
        yield f"redis://{r.get_container_host_ip()}:{r.get_exposed_port(6379)}"


@pytest.fixture
def signatures():
    """Load test signatures from the signatures.json file."""
    import json
    from pathlib import Path
    sig_path = Path(__file__).parent.parent / "techdetector" / "signatures.json"
    with open(sig_path) as f:
        data = json.load(f)
    return data.get("technologies", [])


@pytest.fixture
def sample_html():
    """Sample HTML containing detectable technologies."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <script async src="https://www.googletagmanager.com/gtag/js?id=G-ABC123"></script>
        <script src="https://js.stripe.com/v3/"></script>
    </head>
    <body>
        <div id="intercom-container"></div>
    </body>
    </html>
    """


@pytest.fixture
def sample_headers():
    """Sample HTTP headers containing detectable technologies."""
    return {
        "server": "cloudflare",
        "cf-ray": "abc123-SJC",
        "content-type": "text/html",
        "x-powered-by": "Next.js"
    }
