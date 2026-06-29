import { useState, useRef, useEffect, useCallback } from 'react'
import './App.css'
import ChatThread from './components/ChatThread'
import FileUpload from './components/FileUpload'

const API = ''  // Vite dev-server proxies /chat /rag /sql /health → localhost:8000

const SESSION_ID = () => `session_${Date.now()}`

function App() {
  const [messages, setMessages]       = useState([])
  const [sessionId, setSessionId]     = useState(SESSION_ID)
  const [inputText, setInputText]     = useState('')
  const [isLoading, setIsLoading]     = useState(false)
  const [stats, setStats]             = useState({ messages: 0, docs: 0, queries: 0 })
  const [serverOk, setServerOk]       = useState(null)
  const [docsCount, setDocsCount]     = useState(0)
  const inputRef = useRef(null)

  // ── Health check ───────────────────────────────────────────────────────────
  useEffect(() => {
    fetch(`${API}/health`)
      .then(r => r.json())
      .then(d => {
        setServerOk(true)
        setDocsCount(d.chroma_docs || 0)
      })
      .catch(() => setServerOk(false))
  }, [])

  // ── Handle send ───────────────────────────────────────────────────────────
  const handleSend = useCallback(async () => {
    const text = inputText.trim()
    if (!text || isLoading) return

    const userMsg = { role: 'user', content: text, id: Date.now() }
    setMessages(prev => [...prev, userMsg])
    setInputText('')
    setIsLoading(true)

    try {
      const res = await fetch(`${API}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `HTTP ${res.status}`)
      }

      const data = await res.json()
      const assistantMsg = {
        role: 'assistant',
        content: data.answer,
        mode: data.mode,
        sources: data.sources || [],
        sql_query: data.sql_query || null,
        raw_rows: data.raw_rows || null,
        confidence: data.confidence,
        id: Date.now() + 1,
      }
      setMessages(prev => [...prev, assistantMsg])
      setStats(s => ({ ...s, messages: s.messages + 1, queries: s.queries + 1 }))
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `⚠️ Error: ${err.message}`,
        mode: 'ERROR',
        sources: [],
        id: Date.now() + 2,
      }])
    } finally {
      setIsLoading(false)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }, [inputText, isLoading, sessionId])

  // ── Keyboard handler ──────────────────────────────────────────────────────
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  // ── New conversation ──────────────────────────────────────────────────────
  const handleNewChat = async () => {
    await fetch(`${API}/chat/${sessionId}`, { method: 'DELETE' }).catch(() => {})
    setMessages([])
    setSessionId(SESSION_ID())
    setStats(s => ({ ...s, messages: 0 }))
    setTimeout(() => inputRef.current?.focus(), 50)
  }

  // ── On doc ingested ───────────────────────────────────────────────────────
  const handleIngestSuccess = (result) => {
    setDocsCount(d => d + (result.chunks_stored || 0))
    setStats(s => ({ ...s, docs: s.docs + 1 }))
  }

  // ── Example queries ───────────────────────────────────────────────────────
  const examples = [
    { label: 'SQL', text: 'How many customers are on the Pro plan?' },
    { label: 'SQL', text: 'Show revenue by region for completed orders' },
    { label: 'RAG', text: 'What is the refund policy?' },
    { label: 'RAG', text: 'What analytics dashboards are available?' },
  ]

  return (
    <div className="app">
      {/* ── Sidebar ──────────────────────────────────────────────────────── */}
      <aside className="sidebar">
        {/* Logo */}
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">🧠</div>
          <div className="sidebar-logo-text">
            <span className="sidebar-logo-title">Analytics Agent</span>
            <span className="sidebar-logo-sub">Powered by Groq · LLaMA 3.1</span>
          </div>
        </div>

        {/* New Chat */}
        <button className="new-chat-btn" onClick={handleNewChat} id="new-chat-btn">
          <span>✦</span> New Conversation
        </button>

        {/* Stats */}
        <div>
          <div className="sidebar-section-label">Session Stats</div>
          <div className="sidebar-stats">
            <div className="stat-card">
              <span className="stat-value">{stats.messages}</span>
              <span className="stat-label">Messages</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{stats.docs}</span>
              <span className="stat-label">Docs Uploaded</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{docsCount}</span>
              <span className="stat-label">Chunks Indexed</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{stats.queries}</span>
              <span className="stat-label">Queries Run</span>
            </div>
          </div>
        </div>

        {/* Mode Legend */}
        <div>
          <div className="sidebar-section-label">Query Modes</div>
          <div className="mode-legend">
            {[
              { label: 'RAG', color: 'var(--accent-blue)', desc: 'Answers from uploaded documents' },
              { label: 'SQL', color: 'var(--accent-green)', desc: 'Queries the analytics database' },
              { label: 'Hybrid', color: 'var(--accent-purple)', desc: 'Combines docs + database data' },
            ].map(m => (
              <div key={m.label} className="mode-legend-item">
                <div className="mode-legend-dot" style={{ background: m.color }} />
                <div className="mode-legend-info">
                  <span className="mode-legend-name" style={{ color: m.color }}>{m.label}</span>
                  <span className="mode-legend-desc">{m.desc}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* File Upload */}
        <div>
          <div className="sidebar-section-label">Upload Documents</div>
          <FileUpload apiBase={API} onSuccess={handleIngestSuccess} />
        </div>
      </aside>

      {/* ── Main Panel ───────────────────────────────────────────────────── */}
      <main className="main">
        {/* Topbar */}
        <div className="topbar">
          <div>
            <div className="topbar-title">
              <span className="status-dot" style={{ background: serverOk === false ? 'var(--accent-rose)' : 'var(--accent-green)' }} />
              Conversational Analytics
            </div>
            <div className="topbar-subtitle">
              {serverOk === false ? '⚠️ Backend offline — start uvicorn' : 'Ask questions about your documents or database'}
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <span className="badge badge-rag">RAG</span>
            <span className="badge badge-sql">SQL</span>
            <span className="badge badge-hybrid">Hybrid</span>
          </div>
        </div>

        {/* Chat Thread */}
        <ChatThread
          messages={messages}
          isLoading={isLoading}
          examples={examples}
          onExampleClick={(text) => { setInputText(text); setTimeout(() => inputRef.current?.focus(), 50) }}
        />

        {/* Input Bar */}
        <div style={{
          padding: '16px 24px',
          borderTop: '1px solid var(--border)',
          background: 'var(--bg-glass)',
          backdropFilter: 'blur(20px)',
          display: 'flex',
          gap: 12,
          alignItems: 'flex-end',
        }}>
          <textarea
            ref={inputRef}
            id="chat-input"
            className="input"
            value={inputText}
            onChange={e => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your documents or data... (Enter to send, Shift+Enter for newline)"
            rows={1}
            style={{
              resize: 'none',
              minHeight: 46,
              maxHeight: 140,
              overflow: 'auto',
              paddingTop: 12,
              paddingBottom: 12,
              lineHeight: 1.5,
            }}
            onInput={e => {
              e.target.style.height = 'auto'
              e.target.style.height = Math.min(e.target.scrollHeight, 140) + 'px'
            }}
            disabled={isLoading}
          />
          <button
            id="send-btn"
            className="btn btn-primary"
            onClick={handleSend}
            disabled={isLoading || !inputText.trim()}
            style={{ flexShrink: 0, height: 46, padding: '0 20px', fontSize: 15 }}
          >
            {isLoading ? '⏳' : '↑'}
          </button>
        </div>
      </main>
    </div>
  )
}

export default App
