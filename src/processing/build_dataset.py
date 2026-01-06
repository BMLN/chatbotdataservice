from inference.providers.deepinfra import DeepInfraClient

from os import path

import pandas as pd
from numpy import nan
import json


MAX_CHARS_PER_FIELD = 3000   # pro Textfeld kürzen
MODEL = "openai/gpt-oss-120b"





generator = DeepInfraClient(MODEL)





def truncate(text: str, max_chars: int = MAX_CHARS_PER_FIELD) -> str:
    if not isinstance(text, str):
        return ""
    text = text.strip()
    if len(text) > max_chars:
        return text[:max_chars]
    return text


def __build_problem_raw(row):
    parts = []
    comment_cols = [c for c in row.index if c.startswith("Kommentieren")]
    customer_comment_cols = comment_cols[1::2]

    if pd.notna(row["Zusammenfassung"]):
        parts.append(str(row["Zusammenfassung"]))
    if pd.notna(row.get("Beschreibung")):
        parts.append(str(row["Beschreibung"]))

    for c in customer_comment_cols:
        val = row.get(c)
        if pd.notna(val):
            parts.append(str(val))

    return truncate("\n\n".join(parts).strip())


def __build_solution_raw(row):
    comments = []

    comment_cols = [c for c in row.index if c.startswith("Kommentieren")]
    support_comment_cols = comment_cols[0::2]

    for c in support_comment_cols:
        val = row.get(c)
        if pd.notna(val):
            comments.append(str(val))

    if not comments:
        return ""

    return truncate("\n\n".join(comments).strip())


def build_prompt(id, problem, solution):
    __prompt = f"""Du bist ein Support-Analyst.

Du erhältst ein Support-Ticket und sollst für das Ticket zwei Felder erzeugen:
- "problem": Das Kernproblem des Kunden in 1–3 Sätzen.
- "solution": Eine knappe, vollständige Antwort/Lösung in 2–5 Sätzen.

Regeln:
- Schreibe alles auf Deutsch.
- Entferne Namen, Ticketnummern, interne Links und Signaturen.
- Konzentriere dich nur auf fachlich/technisch Relevantes.
- Antworte AUSSCHLIESSLICH im JSON-Lines-Format, genau in diesem Schema:
{{"id": <ID>, "problem": "...", "solution": "..."}}
- Wenn es im Support-Text keine echte Lösung gibt, antworte AUSSCHLIESSLICH mit einer leeren Antwort im JSON-Lines-Format, genau in dem Schema: 
{{}}

WICHTIG:
- Gib KEINE zusätzlichen Erklärungen, KEINEN Fließtext und KEINE Kommentare außerhalb der JSON-Lines aus.

Hier ist as Ticket:\n
"""
    __prompt = f"""Du bist ein Support-Analyst.

Du erhältst ein Support-Ticket und sollst für das Ticket zwei Felder erzeugen:
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

Output-Format:
- Antworte AUSSCHLIESSLICH im JSON-Lines-Format: eine Zeile pro Ticket, genau in diesem Schema:
  {{"id": <ID>, "problem": "...", "solution": "..."}}
  - Wenn es im Support-Text keine echte Lösung gibt, antworte AUSSCHLIESSLICH mit einer leeren Antwort im JSON-Lines-Format, genau in dem Schema: 
{{}}
- <ID> ist immer die übergebene Ticket-ID.
- Gib KEINE zusätzlichen Erklärungen, KEINEN Fließtext und KEINE Kommentare außerhalb der JSON-Lines aus.
"""

    tickets_string = f"TICKET ID {id}\nKundentext:\n\"\"\"{problem}\"\"\"\nSupport-Text:\n\"\"\"{solution}\"\"\"\n"
    

    return __prompt + tickets_string



def generate(prompt: str) -> str:
    return  generator.generate(
        **{"prompt": prompt}
    )
    

def unparse(str):
    try:
        return json.loads(str)

    except:
        return {}
    

#TODO: jsonification + problem/solution
def process_df(df, output): 
    assert "problem_raw" in df
    assert "solution_raw" in df

    instructions = pd.Series([ build_prompt(*x) for x in zip(df.index, df["problem_raw"], df["solution_raw"]) ])


    generation = instructions.apply(generate)
    generation = generation.apply(unparse).apply(pd.Series)
    
    if not "problem" in generation:
        generation["problem"] = nan

    if not "solution" in generation:
        generation["solution"] = nan
        
    df["problem"] = generation["problem"]
    df["solution"] = generation["solution"]

    df.to_csv(output, mode="a", index=False, header=not path.isfile(output))




def process_csv(csv_file, output_file, batch_size=100):
    
    index = 0
    index_it = 0

    #dis kinda not so clean
    if path.isfile(output_file):
        with open(output_file, mode="r") as f:
            for x in pd.read_csv(output_file, chunksize=batch_size):
                index += len(x)
                

    try:
        for i, x in enumerate(pd.read_csv(csv_file, chunksize=batch_size)):
            if index_it < index:
                index_it += len(x)
                continue

            print(f"processing batch {1 + i}...")
            process_df(x, output=output_file)

        print(f"finished processing {csv_file}")
        

    except KeyboardInterrupt:
        print("interrupted")
        pass







#TODO
if __name__ == "__main__":
    file = ""
    output = ""

    process_csv(file, output)