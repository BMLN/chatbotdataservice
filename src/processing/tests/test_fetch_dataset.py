import pytest
from unittest.mock import MagicMock, patch
from src.processing.fetch_dataset import (
    is_support_author,
    truncate,
    strip_signatures_and_links,
    adf_to_text,
    build_problem_solution_raw
)


# --- Unit Tests für die Hilfsfunktionen ---

def test_is_support_author():
    # Teste bekannte Support-ID (aus deinem Code: 5e5e24b1459a810c9af29a67)
    assert is_support_author({"accountId": "5e5e24b1459a810c9af29a67"}) is True
    # Teste fremde ID
    assert is_support_author({"accountId": "user-123"}) is False
    # Teste leeren Autor
    assert is_support_author(None) is False


def test_truncate():
    text = "A" * 10
    assert truncate(text, max_chars=5) == "AAAAA"
    assert truncate(text, max_chars=20) == "AAAAAAAAAA"
    assert truncate(None) == ""


def test_strip_signatures_and_links():
    text = "Hier ist ein Link https://google.com\n--\nSignatur"
    cleaned = strip_signatures_and_links(text)
    # Link und Signatur nach '--' sollten weg sein
    assert "https" not in cleaned
    assert "Signatur" not in cleaned
    assert cleaned == "Hier ist ein Link"


def test_adf_to_text():
    # ADF ist ein verschachteltes Dict
    adf = {
        "version": 1,
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": "Hallo Welt"}]
            }
        ]
    }
    assert adf_to_text(adf) == "Hallo Welt"


# --- Integration Test mit Mocks ---

def test_build_problem_solution_raw():
    mock_issue = {
        "key": "SWELIB-1",
        "fields": {
            "summary": "Test Titel",
            "description": "Problembeschreibung",
            "comment": {
                "comments": [
                    {
                        "author": {"accountId": "customer-1"},
                        "body": "Zusatzinfo vom Kunden"
                    },
                    {
                        "author": {"accountId": "5e5e24b1459a810c9af29a67"},  # Support ID
                        "body": "Lösung vom Support"
                    }
                ]
            }
        }
    }

    problem, solution = build_problem_solution_raw(mock_issue)

    assert "Test Titel" in problem
    assert "Zusatzinfo vom Kunden" in problem
    assert "Lösung vom Support" in solution
    assert "Lösung vom Support" not in problem


@patch('src.processing.fetch_dataset.servicedesk.Jira')
def test_fetch_details_mock(mock_jira_class):
    # Simuliert die Antwort der Jira API
    mock_instance = mock_jira_class.return_value
    mock_instance.call.return_value = {
        "issues": [{"id": "1", "key": "KEY-1", "fields": {}}]
    }

    from src.processing.fetch_dataset import fetch_details
    result = fetch_details(["KEY-1"], "url", "email", "token", "proj")

    assert len(result) == 1
    assert result[0]["key"] == "KEY-1"