import { useState } from 'react'
import './SourceChips.css'

/**
 * SourceChips — renders citation chips for RAG source documents.
 * Each chip shows "filename — page N".
 * Clicking a chip expands/collapses the source text snippet.
 */
export default function SourceChips({ sources }) {
  const [expanded, setExpanded] = useState(null)   // chunk_id of the open chip

  if (!sources || sources.length === 0) return null

  const toggle = (chunkId) =>
    setExpanded(prev => (prev === chunkId ? null : chunkId))

  return (
    <div className="source-chips-container">
      <div className="source-chips-label">
        <span className="source-chips-icon">📎</span>
        Sources ({sources.length})
      </div>

      <div className="source-chips-row">
        {sources.map((src, i) => {
          const label = src.page
            ? `${src.doc_name} — page ${src.page}`
            : src.doc_name
          const isOpen = expanded === src.chunk_id

          return (
            <div key={src.chunk_id || i} className="source-chip-wrapper">
              <button
                id={`source-chip-${src.chunk_id || i}`}
                className={`source-chip ${isOpen ? 'source-chip--open' : ''}`}
                onClick={() => toggle(src.chunk_id)}
                title="Click to expand source excerpt"
              >
                <span className="source-chip-icon">{src.page ? '📄' : '🗂️'}</span>
                <span className="source-chip-label">{label}</span>
                <span className="source-chip-caret">{isOpen ? '▲' : '▼'}</span>
              </button>

              {/* Expandable snippet */}
              {isOpen && src.snippet && (
                <div className="source-snippet animate-fade-in">
                  <div className="source-snippet-meta">
                    <strong>{src.doc_name}</strong>
                    {src.page && <span> · Page {src.page}</span>}
                  </div>
                  <p className="source-snippet-text">{src.snippet}</p>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
