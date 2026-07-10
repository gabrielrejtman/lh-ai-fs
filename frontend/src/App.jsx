import { useState } from 'react'

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
      console.log("Dados recebidos do backend:", data) // Ajuda a debugar no F12
      setReport(data.report || data) // Garante que pega o report mesmo se a estrutura do json mudar ligeiramente
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Funções de segurança para garantir que não tentamos dar .map em algo que não é array
  const citations = Array.isArray(report?.citations) ? report.citations : []
  const findings = Array.isArray(report?.cross_document_findings) ? report.cross_document_findings : []

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
          backgroundColor: '#0066cc',
          color: 'white',
          border: 'none',
          borderRadius: '5px'
        }}
      >
        {loading ? 'Analyzing...' : 'Run Analysis'}
      </button>

      {error && (
        <div style={{ marginTop: '20px', color: 'red', background: '#ffebee', padding: '15px', borderRadius: '8px' }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {report && (
        <div style={{ marginTop: '30px' }}>
          <h2>Report</h2>

          {/* Renderização Segura do Summary (Pydantic) */}
          {report.summary?.executive_summary && (
            <div style={{ marginBottom: '30px', background: '#f8f9fa', padding: '20px', borderRadius: '10px', borderLeft: '4px solid #0066cc' }}>
              <h3 style={{ marginTop: 0, color: '#0066cc' }}>Executive Summary</h3>
              <p style={{ fontSize: '16px', lineHeight: 1.6 }}>
                {report.summary.executive_summary}
              </p>
              
              <div style={{ display: 'flex', gap: '20px', marginTop: '16px' }}>
                <div style={{ background: '#ffebee', padding: '10px 15px', borderRadius: '8px', color: '#c62828', fontWeight: 'bold' }}>
                  Critical Flaws: {report.summary.critical_flaws_count || 0}
                </div>
                <div style={{ background: '#fff3e0', padding: '10px 15px', borderRadius: '8px', color: '#ef6c00', fontWeight: 'bold' }}>
                  Unverified Claims: {report.summary.unverified_claims_count || 0}
                </div>
              </div>

              {Array.isArray(report.summary.key_warnings) && report.summary.key_warnings.length > 0 && (
                <div style={{ marginTop: '16px' }}>
                  <strong>Key Warnings:</strong>
                  <ul style={{ marginTop: '8px', paddingLeft: '20px' }}>
                    {report.summary.key_warnings.map((warning, idx) => (
                      <li key={idx} style={{ marginBottom: '4px' }}>{warning}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Renderização Segura das Citations */}
          {citations.length > 0 && (
            <div style={{ marginBottom: '30px' }}>
              <h3>Citation Findings</h3>
              <div style={{ display: 'grid', gap: '14px' }}>
                {citations.map((citation, index) => (
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
                      <strong>Status:</strong> <span style={{ color: citation.status === 'contradicted' ? 'red' : 'inherit' }}>{citation.status}</span>
                      {' • '}
                      <strong>Confidence:</strong> {citation.confidence}
                    </div>
                    <div style={{ color: '#333', marginBottom: '8px' }}>
                      {citation.reason}
                    </div>
                    {citation.evidence && (
                      <div style={{ background: '#f7f7f7', padding: '10px', borderRadius: '8px', color: '#333', fontSize: '0.9em' }}>
                        <strong>Evidence:</strong>
                        <div style={{ whiteSpace: 'pre-wrap', marginTop: '6px' }}>{citation.evidence}</div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Renderização Segura das Cross-Document Findings */}
          {findings.length > 0 && (
            <div style={{ marginBottom: '30px' }}>
              <h3>Cross-Document Findings</h3>
              <div style={{ display: 'grid', gap: '14px' }}>
                {findings.map((finding, index) => (
                  <div
                    key={index}
                    style={{
                      border: '1px solid #ddd',
                      borderRadius: '10px',
                      padding: '16px',
                      background: '#fff',
                      borderLeft: finding.severity === 'critical' ? '4px solid #c62828' : '1px solid #ddd'
                    }}
                  >
                    <div style={{ fontWeight: '600', marginBottom: '8px', color: '#c62828' }}>{finding.issue || 'Finding'}</div>
                    <div style={{ fontWeight: '500', marginBottom: '8px' }}>{finding.summary}</div>
                    <div style={{ color: '#555', marginBottom: '8px', fontSize: '0.9em' }}>
                      <strong>Severity:</strong> {finding.severity}
                    </div>
                    {finding.evidence && (
                      <div style={{ background: '#f7f7f7', padding: '10px', borderRadius: '8px', fontSize: '0.9em' }}>
                        <strong>Evidence:</strong>
                        <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontFamily: 'inherit', marginTop: '6px' }}>
                          {typeof finding.evidence === 'string' ? finding.evidence : JSON.stringify(finding.evidence, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Fallback caso não venha nada estruturado */}
          {!report.summary?.executive_summary && citations.length === 0 && findings.length === 0 && (
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
    </div>
  )
}

export default App