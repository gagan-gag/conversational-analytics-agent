import { useEffect, useRef } from 'react'
import SourceChips from './SourceChips'
import './ChatThread.css'

const MODE_CONFIG = {
  RAG:    { label: 'RAG',    cls: 'badge-rag',    icon: '📄' },
  SQL:    { label: 'SQL',    cls: 'badge-sql',    icon: '🗄️' },
  Hybrid: { label: 'Hybrid', cls: 'badge-hybrid', icon: '⚡' },
  ERROR:  { label: 'Error',  cls: 'badge-error',  icon: '⚠️' },
}

function TypingIndicator() {
  return (
    <div className="message-row message-row--assistant animate-fade-up">
      <div className="message-avatar message-avatar--assistant">🤖</div>
      <div className="typing-indicator">
        <span /><span /><span />
      </div>
    </div>
  )
}

function SqlBlock({ sql }) {
  if (!sql) return null
  return (
    <div className="sql-block">
      <div className="sql-block-header">
        <span className="sql-block-label">🗄️ Generated SQL</span>
      </div>
      <pre className="sql-block-code"><code>{sql}</code></pre>
    </div>
  )
}

function DataTable({ rows }) {
  if (!rows || rows.length === 0) return null
  const cols = Object.keys(rows[0])
  return (
    <div className="data-table-wrapper">
      <div className="data-table-header">
        <span className="sql-block-label">📊 Results — {rows.length} row{rows.length !== 1 ? 's' : ''}</span>
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>{cols.map(c => <th key={c}>{c}</th>)}</tr>
          </thead>
          <tbody>
            {rows.slice(0, 50).map((row, i) => (
              <tr key={i}>
                {cols.map(c => (
                  <td key={c}>
                    {typeof row[c] === 'number'
                      ? Number.isInteger(row[c]) ? row[c].toLocaleString() : row[c].toFixed(2)
                      : String(row[c] ?? '—')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length > 50 && (
          <div className="data-table-overflow">
            Showing 50 of {rows.length} rows
          </div>
        )}
      </div>
    </div>
  )
}

function MessageBubble({ msg }) {
  const isUser = msg.role === 'user'
  const modeCfg = MODE_CONFIG[msg.mode] || null

  return (
    <div className={`message-row message-row--${isUser ? 'user' : 'assistant'} animate-fade-up`}>
      {!isUser && (
        <div className="message-avatar message-avatar--assistant">🤖</div>
      )}

      <div className={`message-bubble message-bubble--${isUser ? 'user' : 'assistant'}`}>
        {/* Mode badge */}
        {!isUser && modeCfg && (
          <div className="message-meta">
            <span className={`badge ${modeCfg.cls}`}>
              {modeCfg.icon} {modeCfg.label}
            </span>
            {msg.confidence != null && (
              <span className="confidence-pill">
                {Math.round(msg.confidence * 100)}% confidence
              </span>
            )}
          </div>
        )}

        {/* Content */}
        <div className="message-content">
          {msg.content.split('\n').map((line, i) => (
            <span key={i}>{line}{i < msg.content.split('\n').length - 1 ? <br /> : null}</span>
          ))}
        </div>

        {/* SQL block */}
        {msg.sql_query && <SqlBlock sql={msg.sql_query} />}

        {/* Data table */}
        {msg.raw_rows && msg.raw_rows.length > 0 && <DataTable rows={msg.raw_rows} />}

        {/* Source chips */}
        {msg.sources && msg.sources.length > 0 && (
          <SourceChips sources={msg.sources} />
        )}
      </div>

      {isUser && (
        <div className="message-avatar message-avatar--user">👤</div>
      )}
    </div>
  )
}

function EmptyState({ examples, onExampleClick }) {
  return (
    <div className="empty-state animate-fade-in">
      <div className="empty-state-icon">🧠</div>
      <h2 className="empty-state-title">What would you like to know?</h2>
      <p className="empty-state-desc">
        Ask questions in natural language — I'll automatically decide whether
        to search your documents, query the database, or both.
      </p>
      <div className="example-grid">
        {examples.map((ex, i) => (
          <button
            key={i}
            className="example-card"
            onClick={() => onExampleClick(ex.text)}
            id={`example-${i}`}
          >
            <span className={`badge badge-${ex.label.toLowerCase()}`}>{ex.label}</span>
            <span className="example-text">{ex.text}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

export default function ChatThread({ messages, isLoading, examples, onExampleClick }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  return (
    <div className="chat-thread" id="chat-thread">
      {messages.length === 0 && !isLoading ? (
        <EmptyState examples={examples} onExampleClick={onExampleClick} />
      ) : (
        <div className="messages-list">
          {messages.map(msg => (
            <MessageBubble key={msg.id} msg={msg} />
          ))}
          {isLoading && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>
      )}
    </div>
  )
}
