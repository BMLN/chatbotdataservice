import os
import time
from openai import OpenAI

# ----------------------------
# Konfiguration
# ----------------------------
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
BASE_URL = os.getenv("OPENAI_BASE_URL")  # optional für später (z.B. DeepInfra)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=BASE_URL,
)

# ----------------------------
# Statischer Prefix (Support-Rolle)
# ----------------------------
SUPPORT_PREFIX = """
Du bist Support-Mitarbeiter eines Softwareprodukts.
Stil & Regeln:
- Sprich den Kunden direkt an (Du-Form).
- Sei höflich, ruhig und lösungsorientiert.
- Stelle Rückfragen, wenn Informationen fehlen (max. 3 präzise Fragen).
- Wenn du keine sichere Lösung weißt, sag das ehrlich und schlage sinnvolle nächste Schritte vor.
- Gib konkrete, umsetzbare Schritte (nummeriert).
- Keine ausgedachten Fakten, keine falschen Versprechen.
Antwortformat:
1) Kurze Zusammenfassung des Problems
2) Lösungsschritte
3) Falls nötig: Rückfragen / nächste Schritte
""".strip()

# Damit Prompt Caching gut greift: großer, stabiler Block VORNE.
# Wichtig: Dieser Block muss zwischen Requests exakt identisch bleiben.
# (Hier absichtlich "aufgebläht" für Demo-Zwecke.)
STABLE_CONTEXT = (
    "[STABILER_KONTEXT] Produkt: ExampleApp. Plattform: Windows/macOS/Linux. "
    "Typische Themen: Login, Installation, Performance, Sync, API, Billing. "
    "Support-Policy: Keine Passwörter erfragen, keine sensiblen Daten speichern. "
    "Wenn Logs nötig: nur anonymisierte Auszüge anfordern.\n"
) * 250

DEVELOPER_CONTENT = SUPPORT_PREFIX + "\n\n" + STABLE_CONTEXT.strip()

# Optional: kleine Conversation-History (damit Antworten kontextueller sind)
MAX_TURNS_IN_MEMORY = 6  # zählt User+Assistant Paare (6 = recht klein, aber praxisnah)


def extract_usage_numbers(resp):
    """Robust für unterschiedliche SDK-Felder (prompt_tokens vs input_tokens)."""
    usage = getattr(resp, "usage", None)
    if not usage:
        return None, None, None

    prompt_tokens = getattr(usage, "input_tokens", None) or getattr(usage, "prompt_tokens", None)
    total_tokens = getattr(usage, "total_tokens", None)

    details = getattr(usage, "input_tokens_details", None) or getattr(usage, "prompt_tokens_details", None)
    cached_tokens = getattr(details, "cached_tokens", None) if details else None

    return prompt_tokens, total_tokens, cached_tokens


def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("Fehlt: OPENAI_API_KEY als Environment Variable setzen.")

    print(f"Model: {MODEL}")
    print(f"Base URL: {BASE_URL or '(OpenAI default)'}")
    print("Tipps: 'exit' beendet, 'reset' löscht Gesprächskontext.\n")

    # Messages starten immer gleich => guter Kandidat für Prompt Caching
    messages = [{"role": "developer", "content": DEVELOPER_CONTENT}]

    # stabiler Cache-Key (hilft bei konsistenter Wiederverwendung)
    cache_key = "support-cli-demo-v1"

    while True:
        user_text = input("Kunde> ").strip()
        if not user_text:
            continue
        if user_text.lower() in {"exit", "quit"}:
            break
        if user_text.lower() == "reset":
            messages = [{"role": "developer", "content": DEVELOPER_CONTENT}]
            print("System> Kontext zurückgesetzt.\n")
            continue

        messages.append({"role": "user", "content": user_text})

        # History begrenzen (Developer bleibt immer an Index 0)
        # Wir behalten die letzten MAX_TURNS_IN_MEMORY*2 Nachrichten (user+assistant),
        # plus die Developer-Nachricht am Anfang.
        if len(messages) > 1 + (MAX_TURNS_IN_MEMORY * 2):
            messages = [messages[0]] + messages[-(MAX_TURNS_IN_MEMORY * 2):]

        t0 = time.perf_counter()
        resp = client.responses.create(
            model=MODEL,
            input=messages,
            prompt_cache_key=cache_key,
        )
        latency_ms = (time.perf_counter() - t0) * 1000.0

        answer = (getattr(resp, "output_text", "") or "").strip()
        messages.append({"role": "assistant", "content": answer})

        prompt_tokens, total_tokens, cached_tokens = extract_usage_numbers(resp)

        print("\nSupport> " + answer)
        print(
            f"\n[debug] latency={latency_ms:,.0f}ms | prompt_tokens={prompt_tokens} | "
            f"total_tokens={total_tokens} | cached_tokens={cached_tokens}\n"
        )

    print("System> Ende.")


if __name__ == "__main__":
    main()
