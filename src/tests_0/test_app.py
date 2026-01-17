import pytest
import os
import io
from unittest.mock import patch, MagicMock


# Wir müssen die Umgebungsvariablen setzen, BEVOR wir die App importieren,
# da die app.py beim Import sofort prüft, ob Variablen wie JIRA_BASEURL da sind.
@pytest.fixture(scope="module")
def test_client():
    with patch.dict(os.environ, {
        "FETCH_TICKETDATA": "True",
        "JIRA_BASEURL": "https://test.atlassian.net",
        "JIRA_AUTH_EMAIL": "test@example.com",
        "JIRA_AUTH_TOKEN": "token123",
        "JIRA_PROJECT": "PROJ",
        "DEEPINFRA_KEY": "key123",
        "ENCODER_MODEL": "test-model",
        "KB_HOST": "localhost",
        "KB_PORT": "8080",
        "KB_COLLECTION": "Test"
    }):
        # Hier mocken wir find_spec, damit Flask denkt, alle Pakete seien installiert
        with patch("importlib.util.find_spec", return_value=MagicMock()):
            from src.app import app
            app.config['TESTING'] = True
            with app.test_client() as client:
                yield client


## --- Tests für die Endpoints ---

def test_fetch_ticketdata_endpoint(test_client):
    """Testet den /fetch_ticketdata GET Endpoint"""
    # Wir mocken die tatsächliche Verarbeitungsfunktion in processing
    with patch("src.processing.fetch_dataset.fetch_dataset") as mock_fetch:
        # Simuliere das Erstellen einer Datei
        mock_fetch.side_effect = lambda file, *args: open(file, 'w').write("id,summary\n1,Test")

        response = test_client.get("/fetch_ticketdata?updated=2026-01-01")

        assert response.status_code == 200
        assert b"id,summary" in response.data


def test_generate_ticketdata_invalid_file(test_client):
    """Prüft, ob der Server 415 zurückgibt, wenn keine CSV gesendet wird"""
    data = {
        'file': (io.BytesIO(b"not a csv"), "test.txt")
    }
    response = test_client.get("/generate_ticketdata", data=data, content_type='multipart/form-data')
    assert response.status_code == 415


def test_load_kbdata_success(test_client):
    """Testet das Hochladen von JSONL Daten"""
    with patch("src.processing.load_dataset.load") as mock_load:
        data = {
            'file': (io.BytesIO(b'{"text": "hallo"}\n'), "kbdata.jsonl")
        }
        response = test_client.post("/load_kbdata", data=data, content_type='multipart/form-data')

        assert response.status_code == 200
        mock_load.assert_called_once()