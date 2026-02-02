import pytest
import pandas as pd
import os
from unittest.mock import patch, MagicMock
from src.processing.encode_dataset import encode


# Fixture für Testdaten
@pytest.fixture
def sample_csv(tmp_path):
    csv_path = tmp_path / "test_input.csv"
    df = pd.DataFrame({
        "problem": ["Ticket 1", "Ticket 2"],
        "issue_key": ["ID-1", "ID-2"],
        "other": ["extra", "info"]
    })
    df.to_csv(csv_path, index=False)
    return str(csv_path)


@patch('src.processing.encode_dataset.HFVectorizer')
@patch('src.processing.encode_dataset.BatchProcessor')
@patch('src.processing.encode_dataset.mkdir')
@patch('src.processing.encode_dataset.copy')
def test_encode_success(mock_copy, mock_mkdir, mock_batch, mock_vectorizer_class, sample_csv, tmp_path):
    import os
    os.makedirs("./.processing/test_input", exist_ok=True)

    # Setup Mocks
    mock_vectorizer = MagicMock()
    mock_vectorizer_class.return_value = mock_vectorizer
    # Simuliere die Vektorisierung: 2 Zeilen -> 2 Listen
    mock_vectorizer.vectorize.return_value = [[0.1, 0.1], [0.2, 0.2]]

    output_file = str(tmp_path / "output.jsonl")

    # Wir müssen den BatchProcessor dazu bringen, unsere Lambda-Funktion auszuführen
    # Da BatchProcessor.process intern die CsvDataframeProcessor.process aufruft,
    # vereinfachen wir das hier, indem wir prüfen, ob die Aufrufe grundsätzlich stimmen.

    # Test-Aufruf
    encode(
        input=sample_csv,
        output=output_file,
        encoder_model="test-model",
        text_column="problem",
        data_columns=["issue_key"]
    )

    # Verifizierung
    mock_vectorizer_class.assert_called_with("test-model")
    mock_batch.process.assert_called_once()
    # Prüfe, ob das Verzeichnis-Handling versucht wurde
    assert mock_mkdir.called


def test_encode_missing_column(sample_csv, tmp_path):
    """Prüft, ob ein Fehler geworfen wird, wenn die Text-Spalte fehlt"""
    with patch('src.processing.encode_dataset.HFVectorizer'):
        output_file = str(tmp_path / "output.jsonl")

        # In der encode Funktion wird im Fehlerfall ein ValueError geworfen
        # Wir müssen hier manuell ein DF an die innere Funktion übergeben oder
        # den Fehler im Integrations-Kontext provozieren.

        with pytest.raises(Exception):  # BatchProcessor wird scheitern oder ValueError fliegen
            encode(
                input=sample_csv,
                output=output_file,
                encoder_model="test-model",
                text_column="falsche_spalte",  # Diese Spalte existiert nicht
                data_columns=["issue_key"]
            )