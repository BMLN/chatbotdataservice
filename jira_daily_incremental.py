#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
jira_daily_incremental.py

Zieht alle heute (UTC) aktualisierten Jira-Vorgänge per API, verarbeitet nur neue (noch nicht
im Output vorhandene) Tickets, generiert problem/solution via OpenAI und hängt die Ergebnisse
an eine bestehende End-CSV an.

Voraussetzungen:
  pip install requests pandas openai

Umgebungsvariablen:
  JIRA_BASE_URL="https://<dein-domain>.atlassian.net"
  JIRA_EMAIL="you@company.com"
  JIRA_API_TOKEN="xxxx"
  OPENAI_API_KEY="sk-..."

Konfiguration im Script:
  - JQL_PROJECT (Projekt/Filter)
  - Support-Erkennung (SUPPORT_*)

Outputs:
  - FINAL_OUTPUT_FILE: wird erweitert (append)
  - STATE_FILE: merkt bereits verarbeitete issue_keys (Duplikate vermeiden)
"""

import os
import json
import time
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests
import pandas as pd
from openai import OpenAI

# =========================
# Konfiguration
# =========================

# Jira
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "").rstrip("/")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")

# JQL: Projekt / Basisfilter
JQL_PROJECT = "project = SWELIB"

# "Heute" – wir ziehen alles, was seit Tagesbeginn (UTC) aktualisiert wurde
# Jira JQL erwartet "YYYY-MM-DD HH:MM"
def today_utc_start_jql() -> str:
    now = datetime.now(timezone.utc)
    start = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=timezone.utc)
    return start.strftime("%Y-%m-%d %H:%M")

# OpenAI
client = OpenAI()
MODEL_NAME = "gpt-4.1-mini"
BATCH_SIZE = 20
MAX_CHARS_PER_FIELD = 3000

# Dateien
STATE_FILE = "state.json"
FINAL_OUTPUT_FILE = "data_03/tickets_final.csv"  # wird erweitert

os.makedirs(os.path.dirname(FINAL_OUTPUT_FILE) or ".", exist_ok=True)

# Support-Identifikation (mindestens eine Methode pflegen):
SUPPORT_ACCOUNT_IDS = set([
    "5e5e24b1459a810c9af29a67",
])

SUPPORT_EMAIL_DOMAINS = set([
    # "company.com",
])

SUPPORT_DISPLAYNAME_KEYWORDS = [
    # "Support",
    # "Service Desk",
]

# Jira Fields
JIRA_FIELDS = [
    "summary",
    "description",
    "comment",
    "updated",
]

# =========================
# Prompt (wie bei dir)
# =========================

BATCH_PROMPT_HEADER = """Du bist ein Support-Analyst.

Du erhältst mehrere Support-Tickets und sollst für jedes Ticket zwei Felder erzeugen:
- "problem": Das Kernproblem des Kunden in 1–3 Sätzen, neutral zusammengefasst (3. Person ist hier ok).
- "solution": Eine knappe, vollständige Support-Antwort an den Kunden in 2–5 Sätzen.

Stilregeln (sehr wichtig):
- Schreibe die "solution" IMMER als direkte Antwort an den Kunden (2. Person, Anrede: "Sie").
- Vermeide strikt Formulierungen in der 3. Person über den Kunden, z. B.: "Der Kunde ...", "Kunde muss ...", "Der Benutzer ...".
- Stattdessen: "Bitte ...", "Sie können ...", "Gehen Sie wie folgt vor ...", "Wir empfehlen ...".
- Keine Meta-Anweisungen, keine interne Prozesssprache (z. B. "Ticket eskalieren", "an 2nd Level geben").

Inhaltliche Regeln:
- Schreibe alles auf Deutsch.
- Entferne Namen, Ticketnummern, interne Links und Signaturen.
- Konzentriere dich nur auf fachlich/technisch Relevantes.
- Wenn es im Support-Text keine echte Lösung gibt, schreibe ehrlich, dass keine endgültige Lösung dokumentiert ist und ggf. nur ein Workaround existiert – ebenfalls als direkte Kundenansprache.

Output-Format:
- Antworte AUSSCHLIESSLICH im JSON-Lines-Format: eine Zeile pro Ticket, genau in diesem Schema:
  {"id": <ID>, "problem": "...", "solution": "..."}
- <ID> ist immer die übergebene Ticket-ID.
- Gib KEINE zusätzlichen Erklärungen, KEINEN Fließtext und KEINE Kommentare außerhalb der JSON-Lines aus.
"""

# =========================
# Helpers
# =========================

def truncate(text: Any, max_chars: int = MAX_CHARS_PER_FIELD) -> str:
    if not isinstance(text, str):
        return ""
    t = text.strip()
    return t[:max_chars] if len(t) > max_chars else t

def strip_signatures_and_links(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"https?://\S+", "", text)
    text = re.split(r"(\n--\s*\n|\nMit freundlichen Grüßen|\nBest regards)", text, maxsplit=1)[0]
    return text.strip()

def adf_to_text(node: Any) -> str:
    # Atlassian Document Format -> Text extrahieren
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        parts = []
        if "text" in node and isinstance(node["text"], str):
            parts.append(node["text"])
        for v in node.values():
            if isinstance(v, (dict, list)):
                parts.append(adf_to_text(v))
        return " ".join([p for p in parts if p]).strip()
    if isinstance(node, list):
        return " ".join([adf_to_text(x) for x in node]).strip()
    return ""

def normalize_richtext(field: Any) -> str:
    if field is None:
        return ""
    if isinstance(field, str):
        return field.strip()
    if isinstance(field, (dict, list)):
        return adf_to_text(field).strip()
    return str(field).strip()

def jira_auth() -> Tuple[str, str]:
    return (JIRA_EMAIL, JIRA_API_TOKEN)

def jira_get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = f"{JIRA_BASE_URL}{path}"
    r = requests.get(
        url,
        auth=jira_auth(),
        params=params or {},
        headers={"Accept": "application/json"},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()

def fetch_issues(jql: str) -> List[Dict[str, Any]]:
    """
    1) /search/jql gibt Issue IDs (und ggf. mehr) + nextPageToken
    2) /issue/bulkfetch holt key + fields für diese IDs
    """
    all_issue_ids: List[str] = []
    next_page_token: Optional[str] = None

    while True:
        params = {
            "jql": jql,
            "maxResults": 100,
        }
        if next_page_token:
            params["nextPageToken"] = next_page_token

        data = jira_get("/rest/api/3/search/jql", params=params)

        batch = data.get("issues", []) or []
        # in deinem Test: batch = [{"id": "32391"}]
        for it in batch:
            if isinstance(it, dict) and it.get("id"):
                all_issue_ids.append(str(it["id"]))

        next_page_token = data.get("nextPageToken")
        if not next_page_token or not batch:
            break

    # Details in Chunks nachladen
    issues: List[Dict[str, Any]] = []
    CHUNK = 100
    for i in range(0, len(all_issue_ids), CHUNK):
        chunk_ids = all_issue_ids[i:i+CHUNK]
        issues.extend(fetch_issue_details(chunk_ids))

    return issues


def fetch_issue_details(issue_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Holt vollständige Issue-Objekte (key + fields) per bulk fetch.
    Endpoint: /rest/api/3/issue/bulkfetch
    """
    if not issue_ids:
        return []

    url = f"{JIRA_BASE_URL}/rest/api/3/issue/bulkfetch"
    payload = {
        "issueIdsOrKeys": issue_ids,
        "fields": JIRA_FIELDS,
    }

    r = requests.post(
        url,
        auth=jira_auth(),
        json=payload,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    # Antwort enthält i.d.R. "issues"
    return data.get("issues", []) or []


def load_state() -> Dict[str, Any]:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"processed_issue_keys": []}

def save_state(state: Dict[str, Any]) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def is_support_author(author: Dict[str, Any]) -> bool:
    if not author:
        return False
    account_id = author.get("accountId") or ""
    email = author.get("emailAddress") or ""  # kann in Cloud fehlen
    display = author.get("displayName") or ""

    if account_id and account_id in SUPPORT_ACCOUNT_IDS:
        return True

    if email and "@" in email:
        domain = email.split("@", 1)[1].lower()
        if domain in SUPPORT_EMAIL_DOMAINS:
            return True

    if display:
        dlow = display.lower()
        for kw in SUPPORT_DISPLAYNAME_KEYWORDS:
            if kw.lower() in dlow:
                return True

    return False

def build_problem_solution_raw(issue: Dict[str, Any]) -> Tuple[str, str]:
    fields = issue.get("fields", {}) or {}

    summary = fields.get("summary") or ""
    description = normalize_richtext(fields.get("description"))
    description = strip_signatures_and_links(description)

    comment_obj = fields.get("comment") or {}
    comments = comment_obj.get("comments") or []

    customer_texts: List[str] = []
    support_texts: List[str] = []

    for c in comments:
        body = normalize_richtext(c.get("body"))
        body = strip_signatures_and_links(body)
        if not body:
            continue

        author = c.get("author") or {}
        if is_support_author(author):
            support_texts.append(body)
        else:
            customer_texts.append(body)

    parts_problem = []
    if summary:
        parts_problem.append(str(summary))
    if description:
        parts_problem.append(str(description))
    parts_problem.extend(customer_texts)

    problem_raw = truncate("\n\n".join([p for p in parts_problem if p]).strip())
    solution_raw = truncate("\n\n".join([p for p in support_texts if p]).strip()) if support_texts else ""

    return problem_raw, solution_raw

def build_batch_prompt(batch_rows: List[Dict[str, Any]]) -> str:
    parts = [BATCH_PROMPT_HEADER, "", "Hier sind die Tickets:\n"]
    for row in batch_rows:
        idx = row["id"]
        problem_raw = truncate(row.get("problem_raw", "") or "")
        solution_raw = truncate(row.get("solution_raw", "") or "")

        parts.append(f"TICKET ID {idx}")
        parts.append(f"id: {idx}")
        parts.append("Kundentext:")
        parts.append(f'\"\"\"{problem_raw}\"\"\"')
        parts.append("Support-Text:")
        parts.append(f'\"\"\"{solution_raw}\"\"\"')
        parts.append("")
    return "\n".join(parts)

def call_llm(prompt: str) -> str:
    resp = client.responses.create(
        model=MODEL_NAME,
        input=prompt,
    )
    return (resp.output_text or "").strip()

# =========================
# Main
# =========================

def main():
    if not (JIRA_BASE_URL and JIRA_EMAIL and JIRA_API_TOKEN):
        raise SystemExit("Bitte JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN als Env Vars setzen.")
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("Bitte OPENAI_API_KEY als Env Var setzen.")

    # JQL: nur Tickets, die heute aktualisiert wurden
    since = today_utc_start_jql()
    jql = f'{JQL_PROJECT} AND updated >= "{since}" ORDER BY updated ASC'

    # Duplikate vermeiden: aus state + aus final.csv
    state = load_state()
    processed_keys = set(state.get("processed_issue_keys", []))
    seen_keys = processed_keys


    issues = fetch_issues(jql)

    # Nur neue Keys verarbeiten
    new_issues = [it for it in issues if (it.get("key") and it["key"] not in seen_keys)]

    if not new_issues:
        print("Keine neuen (heute aktualisierten) Tickets zu verarbeiten.")
        return

    # Build rows
    rows: List[Dict[str, Any]] = []
    for i, issue in enumerate(new_issues):
        key = issue.get("key")
        problem_raw, solution_raw = build_problem_solution_raw(issue)
        rows.append({
            "id": i,  # Batch-interne ID
            "issue_key": key,
            "problem_raw": problem_raw,
            "solution_raw": solution_raw,
        })

    df = pd.DataFrame(rows)
    df["problem"] = pd.NA
    df["solution"] = pd.NA

    # LLM batches
    todo_ids = df["id"].tolist()
    for start in range(0, len(todo_ids), BATCH_SIZE):
        batch_ids = todo_ids[start:start + BATCH_SIZE]
        batch_rows = df[df["id"].isin(batch_ids)].to_dict(orient="records")

        prompt = build_batch_prompt(batch_rows)
        raw_out = call_llm(prompt)

        if not raw_out:
            print("Warnung: Leere LLM-Antwort für Batch, übersprungen.")
            continue

        for line in [l for l in raw_out.splitlines() if l.strip()]:
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                print(f"Warnung: JSON nicht parsebar: {line[:200]}")
                continue

            tid = data.get("id")
            prob = (data.get("problem") or "").strip()
            sol = (data.get("solution") or "").strip()

            if tid is None:
                continue

            mask = df["id"] == tid
            if mask.any():
                df.loc[mask, "problem"] = prob
                df.loc[mask, "solution"] = sol

        # Schonung
        time.sleep(0.3)

    # Nur erfolgreich generierte Zeilen anhängen
    df_out = df.dropna(subset=["problem", "solution"]).copy()
    if df_out.empty:
        print("Keine verwertbaren Ergebnisse (problem/solution leer).")
        return

    # Final-Format
    df_final_append = df_out[["problem", "solution"]].copy()

    # Append an FINAL_OUTPUT_FILE
    file_exists = os.path.exists(FINAL_OUTPUT_FILE)
    df_final_append.to_csv(
        FINAL_OUTPUT_FILE,
        mode="a" if file_exists else "w",
        index=False,
        header=not file_exists,
        encoding="utf-8",
    )

    # State updaten
    new_keys = df_out["issue_key"].dropna().astype(str).tolist()
    processed_keys.update(new_keys)
    state["processed_issue_keys"] = sorted(processed_keys)
    save_state(state)

    print(f"Fertig. Angehaengt: {len(df_final_append)} Tickets -> {FINAL_OUTPUT_FILE}")

if __name__ == "__main__":
    main()
