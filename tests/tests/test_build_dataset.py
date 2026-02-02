import pytest
import pandas as pd
import json
from unittest.mock import patch, MagicMock
from src.processing.build_dataset import (
    truncate,
    build_prompt,
    unparse,
    process_df
)


# --- Unit Tests für Hilfsfunktionen ---

def test_truncate_logic():
    assert truncate("   hallo   ") == "hallo"
    assert truncate("A" * 10, max_chars=5) == "AAAAA"
    assert truncate(None) == ""


def test_unparse_json():
    valid_json = '{"id": 1, "problem": "test"}'
    invalid_json = "Kein JSON"
    assert unparse(valid_json)["id"] == 1
    assert unparse(invalid_json) == {}


def test_build_prompt_content():
    prompt = build_prompt(123, "Mein Problem", "Meine Lösung")
    assert "TICKET ID 123" in prompt
    assert "Mein Problem" in prompt
    assert "Du bist ein Support-Analyst" in prompt


# --- Integration Test mit Mocking der KI ---

# Wir patchen direkt das 'generator'-Objekt im Modul build_dataset
@patch('src.processing.build_dataset.generator')
def test_process_df_integration(mock_generator, tmp_path):
    # Setup: Wir sagen dem Mock-Generator, was er zurückgeben soll
    # Wir simulieren hier die Rückgabe der Basis-Klasse 'generate'
    mock_generator.generate.return_value = '{"id": 0, "problem": "Kurz", "solution": "Fix"}'

    # Test-Datenframe erstellen
    df = pd.DataFrame({
        "problem_raw": ["Das ist ein langes Problem"],
        "solution_raw": ["Das ist eine lange Lösung"]
    })

    # Nutze tmp_path von pytest für eine saubere Test-Umgebung
    output_file = tmp_path / "output.csv"

    # Ausführung
    process_df(df, str(output_file))

    # Verifizierung
    result_df = pd.read_csv(output_file)
    assert len(result_df) == 1
    assert result_df.iloc[0]["problem"] == "Kurz"
    assert result_df.iloc[0]["solution"] == "Fix"

    # Optional: Prüfen, ob der Generator wirklich aufgerufen wurde
    assert mock_generator.generate.called