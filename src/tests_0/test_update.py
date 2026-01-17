import pytest
import os
from unittest.mock import patch


# Wir nutzen ein Fixture, um die Umgebungsvariablen für die Tests zu setzen
@pytest.fixture
def mock_env(mocker):
    with patch.dict(os.environ, {
        "DATASERVICE_SERVICEURL": "http://fake-service.local",
        "DATASERVICE_TIMESTAMP": "2026-01-01"
    }):
        yield


def test_update_success(mock_env, requests_mock):
    """Testet einen komplett erfolgreichen Durchlauf von update.py"""
    base_url = "http://fake-service.local"

    # 1. Mock für /fetch_ticketdata
    requests_mock.get(f"{base_url}/fetch_ticketdata", content=b"ticket,data,csv", status_code=200)

    # 2. Mock für /generate_ticketdata
    requests_mock.get(f"{base_url}/generate_ticketdata", content=b"generated,data", status_code=200)

    # 3. Mock für /generate_kbdata
    requests_mock.get(f"{base_url}/generate_kbdata", content=b'{"knowledge": "base"}', status_code=200)

    # 4. Mock für /load_kbdata
    requests_mock.post(f"{base_url}/load_kbdata", status_code=200)

    # Jetzt importieren wir das Modul. Da der Code direkt im Modul-Body steht,
    # wird er beim Import sofort ausgeführt.
    import src.update

    # Überprüfung, ob die finale Umgebungsvariable gesetzt wurde
    assert os.environ["TICKETDATA_SERVICEURL"] == "2026-01-01"


def test_update_api_failure(mock_env, requests_mock):
    """Testet das Verhalten, wenn eine API einen Fehler (z.B. 500) liefert"""
    base_url = "http://fake-service.local"

    # Der erste Call schlägt fehl
    requests_mock.get(f"{base_url}/fetch_ticketdata", status_code=500)

    # Wir fangen den Print-Output ab, da das Skript Fehler nur printet statt zu raisen
    with patch('builtins.print') as mock_print:
        # Modul neu laden (da es beim ersten Test schon im Cache sein könnte)
        import importlib
        import src.update
        importlib.reload(src.update)

        # Prüfen, ob die Fehlermeldung ausgegeben wurde
        mock_print.assert_called_with(pytest.raises(Exception))
        # Oder spezifischer:
        assert any("/fetch_ticketdata: 500" in str(call) for call in mock_print.call_args_list)