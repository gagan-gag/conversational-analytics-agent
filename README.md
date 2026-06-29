<div align="center">

# Conversational Analytics Agent

**Chat with your documents and database using plain English.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-Latest-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vitejs.dev/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20DB-blue?style=flat-square)](https://www.trychroma.com/)
[![Groq](https://img.shields.io/badge/Groq-LLM-black?style=flat-square)](https://groq.com/)

</div>

---

## Overview

Ask a question in plain English. The agent automatically routes it to the right pipeline — no manual mode selection needed.

| Mode | When it's used |
|------|---------------|
| **RAG** | Searching uploaded PDF, CSV, or TXT documents |
| **SQL** | Querying the analytics database |
| **Hybrid** | Combining document retrieval with SQL results |

---

## Features

**Document Intelligence**
- Upload PDF, CSV, and TXT files
- Automatic chunking and local vector embeddings
- Semantic search via ChromaDB
- Source-aware responses

**Database Analytics**
- Natural language → SQL conversion
- Automatic schema understanding
- Read-only query execution with safety guardrails
- SQLite backend

**Chat Experience**
- Multi-session conversations with history
- Automatic routing between RAG and SQL
- One-click new conversation

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Backend | Python 3.10+, FastAPI, Pydantic, SQLAlchemy, SQLite |
| Frontend | React 18, Vite |
| AI | Groq LLM, ChromaDB, Local Embeddings, RAG Pipeline, Text-to-SQL |

---

## Quick Start

### Requirements

- Python 3.10+
- Node.js 18+
- Groq API key — [get one free](https://console.groq.com)

---

### Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Open `backend\.env` and set your Groq API key:

```env
GROQ_API_KEY=your_actual_groq_key_here
OPENAI_API_KEY=
```

> Leave `OPENAI_API_KEY` blank — the app uses local embeddings automatically.

Start the server:

```powershell
uvicorn main:app --reload --port 8000
```

Expected output:

```
INFO | 🚀 Starting Conversational Analytics Agent...
INFO | SQLite DB found at: ./data/analytics.db
INFO | ChromaDB ready — 0 documents in collection
INFO | Uvicorn running on http://127.0.0.1:8000
```

---

### Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

---

## Usage

**Query the database**

```
How many customers are on the Pro plan?
Show revenue by region for completed orders.
Which customers churned last month?
```

**Query uploaded documents**

1. Click **Upload Documents**
2. Upload a PDF, CSV, or TXT file
3. Wait for the **✓ Ingested** confirmation
4. Ask questions:

```
What is the refund policy?
Summarise the key points in the report.
```

**Start fresh** — click **✦ New Conversation** in the sidebar to clear history.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/chat` | Main conversational endpoint |
| `POST` | `/rag/ingest` | Upload documents |
| `POST` | `/rag/query` | Query uploaded documents |
| `POST` | `/sql/query` | Query analytics database |
| `GET` | `/sql/schema` | View database schema |
| `DELETE` | `/chat/{session_id}` | Clear chat session |

Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Project Structure

```
conversational-analytics-agent/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── .env
│   ├── requirements.txt
│   ├── rag/
│   │   ├── ingestor.py
│   │   ├── retriever.py
│   │   └── chain.py
│   ├── sql_agent/
│   │   ├── agent.py
│   │   ├── guardrails.py
│   │   └── schema_loader.py
│   ├── router/
│   │   └── query_router.py
│   └── data/
│       ├── analytics.db
│       └── seed_db.py
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   └── components/
    │       ├── ChatThread/
    │       ├── FileUpload/
    │       └── SourceChips/
    └── vite.config.js
```

---

## Troubleshooting

**Backend offline**
Run `uvicorn main:app --reload --port 8000` again.

**`pip install` fails**
Make sure the virtual environment is active: `.venv\Scripts\Activate.ps1`

**Model not found**
Check that `GROQ_API_KEY` in `backend\.env` contains a valid key.

**ChromaDB / embedding errors**
On first upload, the app downloads the `all-MiniLM-L6-v2` model (~90 MB). Wait for the download to finish before retrying.

---

<div align="center">

Built with FastAPI · React · Groq · ChromaDB · SQLite

</div>
