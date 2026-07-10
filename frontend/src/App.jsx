import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

function App() {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const runAnalysis = async () => {
    setLoading(true)
    setError(null)
    setReport(null)

    try {
      const response = await fetch('http://localhost:8002/analyze', {
        method: 'POST',
      })

      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`)
      }

      const data = await response.json()
      setReport(data.report)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: '800px', margin: '40px auto', padding: '0 20px', fontFamily: 'system-ui, sans-serif' }}>
      <h1>BS Detector</h1>
      <p>Legal brief verification pipeline</p>

      <button
        onClick={runAnalysis}
        disabled={loading}
        style={{
          padding: '10px 24px',
          fontSize: '16px',
          cursor: loading ? 'not-allowed' : 'pointer',
        }}
      >
        {loading ? 'Analyzing...' : 'Run Analysis'}
      </button>

      {error && (
        <div style={{ marginTop: '20px', color: 'red' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {report && (
        <div style={{ marginTop: '20px' }}>
          <h2>Report</h2>

          {report.summary && (
            <div style={{ marginBottom: '24px', lineHeight: 1.7 }}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{report.summary}</ReactMarkdown>
            </div>
          )}

          {report.citations?.length > 0 && (
            <div style={{ marginBottom: '24px' }}>
              <h3>Citation Findings</h3>
              <div style={{ display: 'grid', gap: '14px' }}>
                {report.citations.map((citation, index) => (
                  <div
                    key={index}
                    style={{
                      border: '1px solid #ddd',
                      borderRadius: '10px',
                      padding: '16px',
                      background: '#fff',
                    }}
                  >
                    <div style={{ fontWeight: '600', marginBottom: '8px' }}>
                      {citation.citation}
                    </div>
                    <div style={{ color: '#555', marginBottom: '8px' }}>
                      <strong>Status:</strong> {citation.status}
                      {' • '}
                      <strong>Confidence:</strong> {Math.round(citation.confidence * 100)}%
                    </div>
                    <div style={{ color: '#333', marginBottom: '8px' }}>
                      {citation.reason}
                    </div>
                    {citation.evidence && (
                      <div style={{ background: '#f7f7f7', padding: '10px', borderRadius: '8px', color: '#333' }}>
                        <strong>Evidence:</strong>
                        <div style={{ whiteSpace: 'pre-wrap', marginTop: '6px' }}>{citation.evidence}</div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {report.cross_document_findings?.length > 0 && (
            <div style={{ marginBottom: '24px' }}>
              <h3>Cross-Document Findings</h3>
              <div style={{ display: 'grid', gap: '14px' }}>
                {report.cross_document_findings.map((finding, index) => (
                  <div
                    key={index}
                    style={{
                      border: '1px solid #ddd',
                      borderRadius: '10px',
                      padding: '16px',
                      background: '#fff',
                    }}
                  >
                    <div style={{ fontWeight: '600', marginBottom: '8px' }}>{finding.summary}</div>
                    <div style={{ color: '#555', marginBottom: '8px' }}>
                      <strong>Severity:</strong> {finding.severity}
                    </div>
                    {finding.evidence && (
                      <div style={{ background: '#f7f7f7', padding: '10px', borderRadius: '8px' }}>
                        <strong>Evidence:</strong>
                        <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{JSON.stringify(finding.evidence, null, 2)}</pre>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {!report.summary && !report.citations?.length && !report.cross_document_findings?.length && (
            <pre style={{
              background: '#f5f5f5',
              padding: '20px',
              borderRadius: '4px',
              overflow: 'auto',
              whiteSpace: 'pre-wrap',
              wordWrap: 'break-word',
            }}>
              {JSON.stringify(report, null, 2)}
            </pre>
          )}
        </div>
      )}

      {report === null && !loading && !error && (
        <p style={{ marginTop: '20px', color: '#888' }}>
          Click "Run Analysis" to analyze the case documents.
        </p>
      )}
    </div>
  )
}

export default App
