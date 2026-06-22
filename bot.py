import os
import anthropic
import requests
from datetime import datetime

# ── Config ──────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN  = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

# ── Claude: cerca e riassumi notizie ────────────────────────────────────────
def get_macro_news() -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    today = datetime.now().strftime("%d %B %Y")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        system=(
            "Sei un analista finanziario esperto. "
            "Cerca le ultime notizie di macro-economia e finanza, con focus sui mercati USA. "
            "Siamo alle 15:30 ora italiana, i mercati americani stanno aprendo adesso. "
            "Concentrati su: apertura Wall Street, futures, Fed, tassi, inflazione USA, "
            "dati macro americani del giorno, dollaro, Treasury, S&P500, Nasdaq, Dow Jones, "
            "petrolio, oro, e impatto sui mercati europei. "
            "Rispondi SOLO in italiano, usando la formattazione Telegram: "
            "grassetto con *testo*, elenchi con •. "
            "Struttura così:\n"
            "1. 📰 TITOLO DEL GIORNO\n"
            "2. 🇺🇸 TOP 5 NOTIZIE USA\n"
            "3. 📊 APERTURA WALL STREET (indici, variazioni)\n"
            "4. 💱 MERCATI (dollaro, Treasury 10Y, oro, petrolio)\n"
            "5. 🔭 DA SEGUIRE OGGI\n"
            "Sii conciso ma preciso. Max 500 parole."
        ),
        messages=[{
            "role": "user",
            "content": f"Briefing macro-finanziario USA di oggi {today}, ore 15:30 italiane. "
                       "Wall Street sta aprendo: dimmi tutto."
        }],
    )

    text_parts = [block.text for block in response.content if block.type == "text"]
    return "\n".join(text_parts) if text_parts else "⚠️ Nessun contenuto ricevuto."


# ── Telegram: invia messaggio ────────────────────────────────────────────────
def send_telegram(text: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
    for chunk in chunks:
        resp = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk,
            "parse_mode": "Markdown",
        }, timeout=10)
        resp.raise_for_status()


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"🚀 Avvio briefing — {datetime.now().isoformat()}")
    try:
        news = get_macro_news()
        header = f"🔔 *Briefing Macro-Finanziario* — {datetime.now().strftime('%d/%m/%Y ore 15:30')}\n\n"
        send_telegram(header + news)
        print("✅ Briefing inviato!")
    except Exception as e:
        print(f"❌ Errore: {e}")
        try:
            send_telegram(f"❌ Errore bot: {e}")
        except Exception:
            pass
        raise
