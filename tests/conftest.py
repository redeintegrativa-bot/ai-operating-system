import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: Integration tests with real websites (use -m 'not integration' to skip)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests requiring network access (use -m 'not slow' to skip)"
    )
