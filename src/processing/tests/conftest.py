import os
import pytest

@pytest.fixture(autouse=True)
def mock_env_vars():
    # Setzt einen Fake-Key, damit der Client beim Import nicht abstürzt
    os.environ["DEEPINFRA_API_TOKEN"] = "test_key_abc_123"