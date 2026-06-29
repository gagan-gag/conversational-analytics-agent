# 🧠 Conversational Analytics Agent (SAGA)

An AI assistant that lets you chat with your **documents** and **database** in plain English.  
Ask it anything — it figures out whether to search your uploaded files (RAG), query the database (SQL), or both (Hybrid).

---

## What does it do?

| Mode | What happens |
|------|-------------|
| **RAG** | Searches your uploaded PDF / CSV / TXT files and answers from them |
| **SQL** | Translates your question into SQL and queries the analytics database |
| **Hybrid** | Does both and combines the answers |

The AI automatically picks the right mode — you just ask naturally.

---

## Requirements

- **Python 3.10+**
- **Node.js 18+**
- A free **Groq API key** → https://console.groq.com

---

## Step 1 — Set up the Backend

Open a terminal and run these commands **one by one**:

```powershell
# Go into the backend folder
cd f:\Gagan\PROJECTS\Sage\conversational-analytics-agent\backend

# Create a virtual environment (only needed once)
python -m venv .venv

# Activate it (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Install all packages (takes a few minutes the first time)
pip install -r requirements.txt
```

### Configure your API key

Open `backend\.env` and make sure your Groq key is set:

```
GROQ_API_KEY=your_actual_groq_key_here
```

> **Where to get the key:** Go to https://console.groq.com → API Keys → Create  
> The key starts with `gsk_`

Leave `OPENAI_API_KEY=` **blank** — the app will use free local embeddings automatically.

### Start the backend

```powershell
# Make sure your .venv is activated, then:
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO | __main__ | 🚀 Starting Conversational Analytics Agent SAGA...
INFO | __main__ | SQLite DB found at: ./data/analytics.db
INFO | __main__ | ChromaDB ready — 0 documents in collection
INFO:     Uvicorn running on http://127.0.0.1:8000
```

✅ Backend is running. **Keep this terminal open.**

---

## Step 2 — Set up the Frontend

Open a **second terminal**:

```powershell
# Go into the frontend folder
cd f:\Gagan\PROJECTS\Sage\conversational-analytics-agent\frontend

# Install packages (only needed once)
npm install

# Start the app
npm run dev
```

You should see:
```
  VITE v6.x  ready in ...ms
  ➜  Local:   http://localhost:5173/
```

Open your browser at **http://localhost:5173**

---

## How to Use

### Asking questions about the database
The app comes with a pre-loaded analytics database. Just type questions like:
- *"How many customers are on the Pro plan?"*
- *"Show revenue by region for completed orders"*
- *"Which customers churned last month?"*

### Asking questions about your documents
1. Click **Upload Documents** in the left sidebar
2. Drop in a PDF, CSV, or TXT file
3. Wait for "✓ Ingested" confirmation
4. Ask questions like:
   - *"What is the refund policy?"*
   - *"Summarise the key points in the report"*

### Starting a new conversation
Click **✦ New Conversation** in the sidebar to clear history and start fresh.

---

## Troubleshooting

### "Backend offline" warning in the UI
The backend is not running. Go back to the backend terminal and run `uvicorn main:app --reload --port 8000`.

### pip install fails
Make sure your virtual environment is activated (you should see `(.venv)` at the start of your terminal prompt). If not, run `.venv\Scripts\Activate.ps1` first.

### "Model not found" error
Your Groq API key might be invalid. Check `backend\.env` and make sure `GROQ_API_KEY` is set to your actual key from https://console.groq.com.

### Embedding / ChromaDB errors on first upload
This is normal on first run — it downloads the `all-MiniLM-L6-v2` model (~90 MB) from HuggingFace. Wait for it to finish, then try the upload again.

---

## Project Structure (Quick Reference)

```
conversational-analytics-agent/
├── backend/
│   ├── main.py              ← FastAPI app, all routes defined here
│   ├── config.py            ← Reads settings from .env
│   ├── .env                 ← YOUR API KEYS GO HERE (never commit this)
│   ├── requirements.txt     ← Python packages
│   ├── rag/
│   │   ├── ingestor.py      ← Parses & embeds uploaded files
│   │   ├── retriever.py     ← Searches ChromaDB for relevant chunks
│   │   └── chain.py         ← Builds answer from retrieved chunks
│   ├── sql_agent/
│   │   ├── agent.py         ← Converts questions to SQL and runs them
│   │   ├── guardrails.py    ← Blocks any dangerous SQL (DELETE, DROP, etc.)
│   │   └── schema_loader.py ← Reads the DB schema and feeds it to the LLM
│   ├── router/
│   │   └── query_router.py  ← Decides: RAG, SQL, or Hybrid?
│   └── data/
│       ├── analytics.db     ← Pre-seeded SQLite database
│       └── seed_db.py       ← Script to recreate the database from scratch
└── frontend/
    ├── src/
    │   ├── App.jsx           ← Main UI component
    │   └── components/       ← ChatThread, FileUpload, SourceChips
    └── vite.config.js        ← Dev server config (proxies API calls to backend)
```

---

## API Endpoints (for reference)

| Method | Endpoint | What it does |
|--------|----------|-------------|
| GET | `/health` | Check if backend is running |
| POST | `/chat` | Main chat endpoint (auto-routes) |
| POST | `/rag/ingest` | Upload a document |
| POST | `/rag/query` | Query documents directly |
| POST | `/sql/query` | Query database directly |
| GET | `/sql/schema` | View the database schema |
| DELETE | `/chat/{session_id}` | Clear chat memory |

Full interactive docs: **http://localhost:8000/docs**
