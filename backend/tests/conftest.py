import pytest
import sys
from pathlib import Path
from httpx import AsyncClient

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.db.mongo import mongo

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def client():
    """Create test client for FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Setup test environment (mock MongoDB if needed)."""
    # For now, we'll use the actual MongoDB from .env
    # In production, you'd use a test database or mock
    yield
    # Cleanup after all tests
