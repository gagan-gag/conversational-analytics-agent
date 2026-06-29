````markdown
<div align="center">

# 🧠 Conversational Analytics Agent

**An AI-powered analytics assistant that lets you chat with your documents and database using natural language.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-Latest-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Database-blue?style=for-the-badge)](https://www.trychroma.com/)
[![Groq](https://img.shields.io/badge/Groq-LLM-black?style=for-the-badge)](https://groq.com/)

[📖 Overview](#-overview) •
[✨ Features](#-features) •
[🛠 Tech Stack](#-tech-stack) •
[🚀 Quick Start](#-quick-start) •
[📡 API Reference](#-api-reference) •
[📂 Project Structure](#-project-structure)

</div>

---

# 📖 Overview

The **Conversational Analytics Agent** enables users to interact with both structured databases and unstructured documents using plain English.

Simply ask a question—the AI automatically determines whether to:

- 📄 Search uploaded documents using **Retrieval-Augmented Generation (RAG)**
- 🗄 Query the analytics database using **Text-to-SQL**
- 🔀 Combine both approaches through **Hybrid Retrieval**

No manual mode selection is required.

---

# ✨ Features

## 🤖 Intelligent Query Routing

| Mode | Description |
|------|-------------|
| **RAG** | Searches uploaded PDF, CSV, and TXT documents |
| **SQL** | Converts natural language into SQL queries |
| **Hybrid** | Combines document retrieval and SQL results |

---

## 📂 Document Intelligence

- ✅ Upload PDF, CSV and TXT files
- ✅ Automatic document chunking
- ✅ Local vector embeddings
- ✅ Semantic search with ChromaDB
- ✅ Source-aware responses

---

## 🗄 Database Analytics

- Natural Language → SQL
- Automatic schema understanding
- SQLite analytics database
- SQL safety guardrails
- Read-only query execution

---

## 💬 Chat Experience

- Multi-session conversations
- Context-aware responses
- Automatic routing between RAG & SQL
- Conversation history
- One-click new conversation

---

# 🛠 Tech Stack

<table>
<tr>

<td width="33%" valign="top">

### Backend

- 🐍 Python 3.10+
- ⚡ FastAPI
- 🔐 Pydantic
- 🗃 SQLite
- 🔄 SQLAlchemy

</td>

<td width="33%" valign="top">

### Frontend

- ⚛ React 18
- ⚡ Vite
- 🎨 Modern UI
- 🌐 REST API
- 💬 Chat Interface

</td>

<td width="33%" valign="top">

### AI Stack

- 🤖 Groq LLM
- 📄 RAG Pipeline
- 🧠 ChromaDB
- 🔍 Text-to-SQL
- 📚 Local Embeddings

</td>

</tr>
</table>

---

# 🚀 Quick Start

## Requirements

| Tool | Version |
|------|---------|
| Python | 3.10+ |
| Node.js | 18+ |
| Groq API Key | Required |

Create a free API key:

https://console.groq.com

---

# 🔧 Backend Setup

```powershell
cd backend

python -m venv .venv

.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

---

## Configure Environment Variables

Open:

```
backend\.env
```

Set your Groq API key.

```env
GROQ_API_KEY=your_actual_groq_key_here
```

Leave this blank:

```env
OPENAI_API_KEY=
```

The application automatically uses local embeddings.

---

## Start Backend

```powershell
uvicorn main:app --reload --port 8000
```

Expected output:

```text
INFO | __main__ | 🚀 Starting Conversational Analytics Agent SAGA...
INFO | __main__ | SQLite DB found at: ./data/analytics.db
INFO | __main__ | ChromaDB ready — 0 documents in collection
INFO | Uvicorn running on http://127.0.0.1:8000
```

Backend URL:

```
http://localhost:8000
```

API Docs:

```
http://localhost:8000/docs
```

Keep this terminal running.

---

# 🎨 Frontend Setup

Open another terminal.

```powershell
cd frontend

npm install

npm run dev
```

Open:

```
http://localhost:5173
```

---

# 💬 Usage

## 🗄 Query the Database

Example questions:

- How many customers are on the Pro plan?
- Show revenue by region for completed orders.
- Which customers churned last month?

---

## 📄 Query Documents

1. Click **Upload Documents**
2. Upload PDF, CSV or TXT files
3. Wait for **✓ Ingested**
4. Ask questions like:

- What is the refund policy?
- Summarise the key points in the report.

---

## ✨ Start a New Conversation

Click **✦ New Conversation** from the sidebar to clear chat history and begin a fresh session.

---

# 📡 API Reference

| Method | Endpoint | Description |
|---------|----------|-------------|
| GET | `/health` | Backend health check |
| POST | `/chat` | Main conversational endpoint |
| POST | `/rag/ingest` | Upload documents |
| POST | `/rag/query` | Query uploaded documents |
| POST | `/sql/query` | Query analytics database |
| GET | `/sql/schema` | View database schema |
| DELETE | `/chat/{session_id}` | Clear chat memory |

---

# 🛠 Troubleshooting

### Backend Offline

Start the backend again.

```powershell
uvicorn main:app --reload --port 8000
```

---

### pip install Failed

Activate the virtual environment.

```powershell
.venv\Scripts\Activate.ps1
```

---

### Model Not Found

Verify that:

```env
GROQ_API_KEY=
```

contains a valid Groq API key.

---

### ChromaDB / Embedding Errors

On the first upload, the application downloads the

```
all-MiniLM-L6-v2
```

embedding model (~90 MB).

Wait for the download to complete before retrying.

---

# 📂 Project Structure

```text
conversational-analytics-agent/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── .env
│   ├── requirements.txt
│   │
│   ├── rag/
│   │   ├── ingestor.py
│   │   ├── retriever.py
│   │   └── chain.py
│   │
│   ├── sql_agent/
│   │   ├── agent.py
│   │   ├── guardrails.py
│   │   └── schema_loader.py
│   │
│   ├── router/
│   │   └── query_router.py
│   │
│   └── data/
│       ├── analytics.db
│       └── seed_db.py
│
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   └── components/
    │       ├── ChatThread
    │       ├── FileUpload
    │       └── SourceChips
    │
    └── vite.config.js
```

---

# 📖 Interactive API Documentation

```
http://localhost:8000/docs
```

---

<div align="center">

Built with ❤️ using FastAPI, React, Groq, ChromaDB and SQLite.

⭐ If you found this project useful, consider giving it a star!

</div>
````
