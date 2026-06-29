import { useCallback, useState } from 'react'
import './FileUpload.css'

const ACCEPTED = '.pdf,.csv,.txt,.md'
const MAX_MB = 50

export default function FileUpload({ apiBase, onSuccess }) {
  const [isDragging, setIsDragging]   = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [progress, setProgress]       = useState(0)
  const [toast, setToast]             = useState(null)  // { type: 'success'|'error', msg }

  const showToast = (type, msg) => {
    setToast({ type, msg })
    setTimeout(() => setToast(null), 4000)
  }

  const upload = useCallback(async (file) => {
    // Validate type
    const ext = file.name.split('.').pop().toLowerCase()
    if (!['pdf', 'csv', 'txt', 'md'].includes(ext)) {
      showToast('error', `Unsupported type: .${ext}. Use PDF, CSV, TXT, or MD.`)
      return
    }
    // Validate size
    if (file.size > MAX_MB * 1024 * 1024) {
      showToast('error', `File too large. Maximum is ${MAX_MB} MB.`)
      return
    }

    setIsUploading(true)
    setProgress(10)

    try {
      const formData = new FormData()
      formData.append('file', file)

      // Simulate progress while waiting
      const progressInterval = setInterval(() => {
        setProgress(p => Math.min(p + 15, 85))
      }, 400)

      const res = await fetch(`${apiBase}/rag/ingest`, {
        method: 'POST',
        body: formData,
      })

      clearInterval(progressInterval)
      setProgress(100)

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Upload failed: HTTP ${res.status}`)
      }

      const data = await res.json()
      showToast('success', `✓ Ingested ${data.chunks_stored} chunks from "${data.doc_name}"`)
      onSuccess?.(data)
    } catch (err) {
      showToast('error', err.message)
    } finally {
      setTimeout(() => {
        setIsUploading(false)
        setProgress(0)
      }, 600)
    }
  }, [apiBase, onSuccess])

  // ── Drag handlers ──────────────────────────────────────────────────────────
  const onDragOver  = (e) => { e.preventDefault(); setIsDragging(true) }
  const onDragLeave = (e) => { e.preventDefault(); setIsDragging(false) }
  const onDrop = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) upload(file)
  }, [upload])

  const onFileChange = (e) => {
    const file = e.target.files[0]
    if (file) { upload(file); e.target.value = '' }
  }

  return (
    <div className="file-upload-container">
      {/* Drop zone */}
      <label
        id="file-upload-zone"
        className={`drop-zone ${isDragging ? 'drop-zone--active' : ''} ${isUploading ? 'drop-zone--uploading' : ''}`}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        htmlFor="file-input"
      >
        <input
          id="file-input"
          type="file"
          accept={ACCEPTED}
          onChange={onFileChange}
          disabled={isUploading}
          style={{ display: 'none' }}
        />

        {isUploading ? (
          <div className="upload-progress-state">
            <div className="upload-spinner" />
            <span className="upload-label">Processing...</span>
            <div className="progress-bar-track">
              <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
            </div>
            <span className="upload-pct">{progress}%</span>
          </div>
        ) : (
          <div className="drop-zone-inner">
            <div className={`drop-icon ${isDragging ? 'drop-icon--active' : ''}`}>
              {isDragging ? '📂' : '📎'}
            </div>
            <span className="drop-primary">
              {isDragging ? 'Drop to upload' : 'Drag & drop or click'}
            </span>
            <span className="drop-secondary">PDF · CSV · TXT · MD — up to {MAX_MB} MB</span>
          </div>
        )}
      </label>

      {/* Toast */}
      {toast && (
        <div className={`upload-toast upload-toast--${toast.type}`}>
          {toast.msg}
        </div>
      )}
    </div>
  )
}
