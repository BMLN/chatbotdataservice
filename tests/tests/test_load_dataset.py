import pytest
import os
import pandas as pd
from unittest.mock import patch, MagicMock
from src.processing.load_dataset import preproc, processor, load


# 1. Test für die Hilfsfunktion preproc
def test_preproc():
    # Testet die Umwandlung von Strings (literal_eval)
    assert preproc("[1, 2, 3]") == [1, 2, 3]
    assert preproc('{"key": "value"}') == {"key": "value"}
    # Testet None-Handling
    assert preproc(None) is None
    # Testet unveränderte Rückgabe bei Nicht-Strings
    assert preproc(123) == 123


# 2. Test für den Daten-Prozessor
def test_processor_success():
    # Erstellt ein Mock-Knowledgebase-Objekt
    mock_kb = MagicMock()
    # Erstellt Testdaten als DataFrame
    df = pd.DataFrame({
        "id": ["[1]"],
        "data": ["{'text': 'hello'}"],
        "embedding": ["[0.1, 0.2]"]
    })

    processor(df, mock_kb)

    # Prüft, ob die create-Methode der KB mit den geparsten Daten aufgerufen wurde
    mock_kb.create.assert_called_once()
    args, kwargs = mock_kb.create.call_args
    assert kwargs['embedding'].iloc[0] == [0.1, 0.2]


# 3. Test für die Hauptfunktion load
@patch('src.processing.load_dataset.WeaviateKB')
@patch('src.processing.load_dataset.BatchProcessor')
@patch('src.processing.load_dataset.mkdir')
@patch('src.processing.load_dataset.copy')
def test_load_integration(mock_copy, mock_mkdir, mock_batch, mock_kb_class):
    # Setup
    mock_kb_instance = MagicMock()
    mock_kb_class.return_value = mock_kb_instance

    test_files = ["test.jsonl"]

    # Ausführung
    load(
        files=test_files,
        host="localhost",
        port="8080",
        collection="TestColl",
        batch_size=10,
        designated_load=0.25,
        designated_bytes=1000,
        error_threshold=0.5
    )

    # Verifizierung
    mock_kb_class.assert_called_with("localhost", "localhost",
                                     "TestColl")  # Laut Code wird host zweimal übergeben? Prüfe app.py!
    mock_batch.process.assert_called_once()