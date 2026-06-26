
import os
import requests
import anthropic
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN    = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID  = os.environ["TELEGRAM_CHAT_ID"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

# Orario previsto del briefing (ora italiana = UTC+2)
BRIEFING_ORA      = 15
BRIEFING_MINUTI   = 30
FINESTRA_RECUPERO = 120  # minuti: se siamo entro 2 ore, invia comunque

# File che registra l'ultima data in cui il briefing è stato inviato con successo
LAST_SENT_FILE = Path("/tmp/last_briefing_sent.txt")

# ── Controllo anti-duplicato e finestra di recupero ─────────────────────────
def briefing_gia_inviato_oggi() -> bool:
    """Restituisce True se il briefing di oggi è già stato inviato con successo."""
    if not LAST_SENT_FILE.exists():
        return False
    ultima_data = LAST_SENT_FILE.read_text().strip()
    oggi = datetime.now().strftime("%Y-%m-%d")
    return ultima_data == oggi

def segna_briefing_inviato() -> None:
    """Salva la data di oggi come 'briefing inviato'."""
    LAST_SENT_FILE.write_text(datetime.now().strftime("%Y-%m-%d"))

def siamo_nella_finestra() -> bool:
    """
    Controlla se siamo nell'orario giusto per inviare il briefing.
    Invia se siamo tra le 15:30 e le 17:30 (ora italiana, UTC+2),
    così recuperiamo anche se Render ha saltato la finestra esatta.
    """
    ora_italiana = datetime.now(timezone(timedelta(hours=2)))
    ora_prevista = ora_italiana.replace(
        hour=BRIEFING_ORA,
        minute=BRIEFING_MINUTI,
        second=0,
        microsecond=0
    )
    ora_limite = ora_prevista + timedelta(minutes=FINESTRA_RECUPERO)

    print(f"🕐 Ora italiana attuale: {ora_italiana.strftime('%H:%M')}")
    print(f"🎯 Finestra di invio: {ora_prevista.strftime('%H:%M')} → {ora_limite.strftime('%H:%M')}")

    return ora_prevista <= ora_italiana <= ora_limite

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
            "Rispondi SOLO in italiano, senza alcuna formattazione Markdown. "
            "Non usare asterischi, underscore o altri simboli di formattazione. "
            "Usa solo emoji e testo semplice. "
            "Struttura così:\n"
            "1. TITOLO DEL GIORNO\n"
            "2. TOP 5 NOTIZIE USA\n"
            "3. APERTURA WALL STREET (indici, variazioni)\n"
            "4. MERCATI (dollaro, Treasury 10Y, oro, petrolio)\n"
            "5. DA SEGUIRE OGGI\n"
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
        }, timeout=10)
        resp.raise_for_status()

# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ora_avvio = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print(f"🚀 Bot avviato — {ora_avvio}")

    # 1. Il briefing di oggi è già stato inviato?
    if briefing_gia_inviato_oggi():
        print("✅ Briefing già inviato oggi. Nessuna azione necessaria.")
        raise SystemExit(0)

    # 2. Siamo nella finestra oraria giusta (15:30 → 17:30 ora italiana)?
    if not siamo_nella_finestra():
        print("⏰ Fuori dalla finestra di invio (15:30–17:30 ora italiana). Nessuna azione.")
        raise SystemExit(0)

    # 3. Tutto ok: genera e invia il briefing
    print("📡 Finestra valida — genero il briefing...")
    try:
        news = get_macro_news()
        ora_invio = datetime.now().strftime("%d/%m/%Y ore %H:%M")
        header = f"🔔 Briefing Macro-Finanziario — {ora_invio}\n\n"
        send_telegram(header + news)
        segna_briefing_inviato()
        print("✅ Briefing inviato con successo!")

    except Exception as e:
        messaggio_errore = (
            f"❌ Errore nel briefing del {ora_avvio}\n"
            f"Dettaglio: {e}\n"
            f"Controlla i log di Render per maggiori informazioni."
        )
        print(messaggio_errore)
        try:
            send_telegram(messaggio_errore)
        except Exception as telegram_err:
            print(f"❌ Impossibile inviare nemmeno il messaggio di errore su Telegram: {telegram_err}")
        raise
