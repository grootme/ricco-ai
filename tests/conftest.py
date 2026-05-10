"""
Pytest configuration and fixtures
"""
import asyncio
import os
import pytest

# Set test environment variables
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    from unittest.mock import MagicMock
    settings = MagicMock()
    settings.OPENROUTER_API_KEY = "test-key"
    settings.DATABASE_URL = "sqlite:///test.db"
    return settings
