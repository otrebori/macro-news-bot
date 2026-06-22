# Setup Railway — 5 minuti

## 1. Crea account Railway
Vai su **railway.app** → clicca **"Start a New Project"** → login con GitHub  
(se non hai GitHub, creane uno gratis su github.com — serve solo per il login)

## 2. Crea il progetto
- Clicca **"New Project"** → **"Empty Project"**

## 3. Carica i file
- Clicca **"+ New"** → **"GitHub Repo"**  
  oppure, più semplice: trascina la cartella `macro-news-bot` direttamente nella pagina

## 4. Aggiungi le variabili (le tue credenziali)
Vai su **Variables** e aggiungi queste 3 righe esatte:

| Nome | Valore |
|------|--------|
| `TELEGRAM_TOKEN` | `8658195982:AAFMTqGZh_6JWxMtuoTs6qMuYoq-w31lrSQ` |
| `TELEGRAM_CHAT_ID` | `753789436` |
| `ANTHROPIC_API_KEY` | `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` |

## 5. Deploy
Clicca **"Deploy"** — Railway installa tutto da solo e programma il bot alle 15:30.

## ✅ Fatto!
Da domani alle 15:30 ricevi il briefing su Telegram.  
Per testarlo subito: **Settings** → **Trigger Run**.
