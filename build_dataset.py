import os
import time
import json
import pandas as pd
from openai import OpenAI

# ===========================
#  OpenAI-Client initialisieren
# ===========================
client = OpenAI()

MODEL_NAME = "gpt-4.1-mini"  # bei Bedarf anpassen
MAX_CHARS_PER_FIELD = 3000   # pro Textfeld kürzen
BATCH_SIZE = 20              # Tickets pro Request
INPUT_FILE = "data_02/tickets_reduced.csv"
PARTIAL_OUTPUT_FILE = "data_03/tickets_training_partial.csv"
FINAL_OUTPUT_FILE = "data_03/tickets_final.csv"


def truncate(text: str, max_chars: int = MAX_CHARS_PER_FIELD) -> str:
    if not isinstance(text, str):
        return ""
    text = text.strip()
    if len(text) > max_chars:
        return text[:max_chars]
    return text


# ===========================
#  CSV laden
# ===========================
df = pd.read_csv(INPUT_FILE)

# Wenn Script schon einmal lief und eine Partial-Datei existiert:
if os.path.exists(PARTIAL_OUTPUT_FILE):
    print(f"Gefundene bestehende Partial-Datei: {PARTIAL_OUTPUT_FILE}")
    df_partial = pd.read_csv(PARTIAL_OUTPUT_FILE)
    # sicherstellen, dass Spalten existieren
    for col in ["problem", "solution"]:
        if col not in df_partial.columns:
            df_partial[col] = pd.NA
    df = df_partial

# sicherstellen, dass die Spalten existieren
for col in ["problem", "solution"]:
    if col not in df.columns:
        df[col] = pd.NA

# Kommentarspalten identifizieren
comment_cols = [c for c in df.columns if c.startswith("Kommentieren")]

# 0,2,4,... = Support | 1,3,5,... = Kunde
support_comment_cols = comment_cols[0::2]
customer_comment_cols = comment_cols[1::2]


# ===========================
#  Problem-Rohtext (Kunde)
# ===========================
def build_problem_raw(row):
    parts = []

    if pd.notna(row.get("Zusammenfassung")):
        parts.append(str(row["Zusammenfassung"]))
    if pd.notna(row.get("Beschreibung")):
        parts.append(str(row["Beschreibung"]))

    for c in customer_comment_cols:
        val = row.get(c)
        if pd.notna(val):
            parts.append(str(val))

    return truncate("\n\n".join(parts).strip())


# ===========================
#  Lösungs-Rohtext (Support)
# ===========================
def build_solution_raw(row):
    comments = []
    for c in support_comment_cols:
        val = row.get(c)
        if pd.notna(val):
            comments.append(str(val))

    if not comments:
        return ""

    return truncate("\n\n".join(comments).strip())


if "problem_raw" not in df.columns:
    df["problem_raw"] = df.apply(build_problem_raw, axis=1)
if "solution_raw" not in df.columns:
    df["solution_raw"] = df.apply(build_solution_raw, axis=1)


# ===========================
#  Batch-Prompt
# ===========================

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


def build_batch_prompt(batch_rows):
    """
    batch_rows: Liste von Tupeln (idx, row)
    """
    parts = [BATCH_PROMPT_HEADER, "", "Hier sind die Tickets:\n"]
    for idx, row in batch_rows:
        problem_raw = row.get("problem_raw", "") or ""
        solution_raw = row.get("solution_raw", "") or ""

        problem_raw = truncate(problem_raw)
        solution_raw = truncate(solution_raw)

        parts.append(f"TICKET ID {idx}")
        parts.append(f"id: {idx}")
        parts.append("Kundentext:")
        parts.append(f'\"\"\"{problem_raw}\"\"\"')
        parts.append("Support-Text:")
        parts.append(f'\"\"\"{solution_raw}\"\"\"')
        parts.append("")  # Leerzeile

    return "\n".join(parts)


def call_llm(prompt: str) -> str:
    if not prompt.strip():
        return ""

    response = client.responses.create(
        model=MODEL_NAME,
        input=prompt,
    )
    return (response.output_text or "").strip()


def process_batch(batch_indices):
    """
    Nimmt eine Liste von DataFrame-Indizes, baut Prompt, ruft LLM auf
    und schreibt problem/solution zurück in df.
    """
    batch_rows = [(idx, df.loc[idx]) for idx in batch_indices]
    prompt = build_batch_prompt(batch_rows)
    raw_output = call_llm(prompt)

    if not raw_output:
        print("⚠️ Leere Antwort vom LLM für Batch, wird übersprungen.")
        return

    lines = [l for l in raw_output.splitlines() if l.strip()]

    for line in lines:
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            print(f"⚠️ Konnte Zeile nicht als JSON parsen: {line}")
            continue

        ticket_id = data.get("id")
        problem = data.get("problem", "").strip()
        solution = data.get("solution", "").strip()

        if ticket_id is None:
            print(f"⚠️ Keine ID im JSON: {data}")
            continue

        if ticket_id not in df.index:
            print(f"⚠️ ID {ticket_id} nicht im DataFrame gefunden.")
            continue

        df.at[ticket_id, "problem"] = problem
        df.at[ticket_id, "solution"] = solution


# ===========================
#  Batches durchlaufen
# ===========================
def main():
    # Indizes, die noch KEIN problem/solution haben
    mask_todo = df["problem"].isna() | df["solution"].isna()
    todo_indices = df[mask_todo].index.tolist()

    if not todo_indices:
        print("Keine offenen Tickets mehr zu verarbeiten.")
    else:
        print(f"Zu verarbeitende Tickets: {len(todo_indices)}")

    try:
        for start in range(0, len(todo_indices), BATCH_SIZE):
            batch_indices = todo_indices[start:start + BATCH_SIZE]
            print(f"Verarbeite Batch {start//BATCH_SIZE + 1} mit {len(batch_indices)} Tickets...")

            process_batch(batch_indices)

            # Nach jedem Batch speichern
            df.to_csv(PARTIAL_OUTPUT_FILE, index=False)
            print(f"Zwischenspeicher geschrieben: {PARTIAL_OUTPUT_FILE}")

    except KeyboardInterrupt:
        print("❌ Manuell abgebrochen. Fortschritt gespeichert.")
        df.to_csv(PARTIAL_OUTPUT_FILE, index=False)

    # Am Ende: finale Datei nur mit Problem & Lösung
    df_out = df[["problem", "solution"]]
    df_out.to_csv(FINAL_OUTPUT_FILE, index=False)
    print(f"Fertig! Finale Datei geschrieben: {FINAL_OUTPUT_FILE}")


if __name__ == "__main__":
    main()
