import { useState, useEffect, useRef, useCallback } from 'react'
import {
  Brain, Search, Lightbulb, AlertTriangle, ListChecks, CheckCircle2,
  Database, Zap, Activity, FileText, Terminal, ChevronRight, RefreshCw,
  Clock, Cpu, TrendingUp, Shield, Play, Loader2, Check, X, AlertCircle,
  BarChart3, Layers, GitBranch
} from 'lucide-react'

const AGENTS = [
  { key: 'orchestrator', name: 'Orchestrator', icon: GitBranch, color: '#7c3aed', desc: 'Workflow controller' },
  { key: 'Research Agent', name: 'Research', icon: Search, color: '#00d4ff', desc: 'Market intelligence' },
  { key: 'Strategy Agent', name: 'Strategy', icon: Lightbulb, color: '#f59e0b', desc: 'GTM & recommendations' },
  { key: 'Critic Agent', name: 'Critic', icon: AlertTriangle, color: '#ef4444', desc: 'Logic & validation' },
  { key: 'Planner Agent', name: 'Planner', icon: ListChecks, color: '#10b981', desc: 'Execution roadmap' },
  { key: 'QA Agent', name: 'QA', icon: CheckCircle2, color: '#ec4899', desc: 'Quality assurance' },
  { key: 'memory', name: 'Memory', icon: Database, color: '#6366f1', desc: 'Vector store' },
]

const MODEL_COLORS = {
  'llama-3.3-70b-versatile': '#00d4ff',
  'llama-3.1-8b-instant': '#7c3aed',
}

function AgentCard({ agent, status, latency, tokens, model, isActive }) {
  const Icon = agent.icon
  const statusConfig = {
    pending: { color: '#334155', pulse: false, label: 'Waiting' },
    running: { color: agent.color, pulse: true, label: 'Running' },
    completed: { color: '#00e676', pulse: false, label: 'Done' },
    failed: { color: '#ff4444', pulse: false, label: 'Failed' },
  }[status || 'pending']

  return (
    <div
      style={{
        background: isActive ? `linear-gradient(135deg, #0d1420, ${agent.color}18)` : '#0d1420',
        border: `1px solid ${isActive ? agent.color + '44' : '#1a2740'}`,
        borderRadius: 12,
        padding: '16px',
        transition: 'all 0.3s ease',
        boxShadow: isActive ? `0 0 20px ${agent.color}22` : 'none',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
        <div style={{
          width: 36, height: 36, borderRadius: 8,
          background: `${agent.color}22`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Icon size={18} color={agent.color} />
        </div>
        <div>
          <div style={{ fontWeight: 600, fontSize: 14, color: '#e8f0fe' }}>{agent.name}</div>
          <div style={{ fontSize: 11, color: '#7a90b8' }}>{agent.desc}</div>
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 6 }}>
          {statusConfig.pulse && (
            <div style={{
              width: 8, height: 8, borderRadius: '50%',
              background: agent.color,
              animation: 'pulse-dot 1s infinite',
            }} />
          )}
          <span style={{ fontSize: 11, color: statusConfig.color, fontFamily: 'Space Mono' }}>
            {statusConfig.label}
          </span>
        </div>
      </div>

      {(latency || tokens) && (
        <div style={{ display: 'flex', gap: 12, marginTop: 8, flexWrap: 'wrap' }}>
          {latency && (
            <span style={{ fontSize: 11, color: '#7a90b8', fontFamily: 'Space Mono' }}>
              ⏱ {latency}ms
            </span>
          )}
          {tokens && (
            <span style={{ fontSize: 11, color: '#7a90b8', fontFamily: 'Space Mono' }}>
              🔢 {tokens} tok
            </span>
          )}
          {model && (
            <span style={{
              fontSize: 10, color: MODEL_COLORS[model] || '#7a90b8',
              background: `${MODEL_COLORS[model] || '#7a90b8'}18`,
              padding: '1px 6px', borderRadius: 4, fontFamily: 'Space Mono',
            }}>
              {model?.replace('llama-3.', 'llama-')}
            </span>
          )}
        </div>
      )}
    </div>
  )
}

function LogLine({ log }) {
  const colors = { info: '#7a90b8', error: '#ff4444', warn: '#ffab00' }
  const color = colors[log.level] || colors.info
  return (
    <div style={{ display: 'flex', gap: 10, padding: '3px 0', fontSize: 12 }}>
      <span style={{ color: '#334155', fontFamily: 'Space Mono', flexShrink: 0 }}>
        {log.ts?.slice(11, 19)}
      </span>
      <span style={{
        color, background: `${color}18`,
        padding: '0 5px', borderRadius: 3, flexShrink: 0,
        fontFamily: 'Space Mono', fontSize: 10, textTransform: 'uppercase',
      }}>
        {log.level}
      </span>
      <span style={{ color: '#00d4ff', flexShrink: 0, fontFamily: 'Space Mono' }}>
        [{log.agent}]
      </span>
      <span style={{ color: '#b0c4de' }}>{log.msg}</span>
    </div>
  )
}

function ReportSection({ title, content, icon: Icon, color }) {
  const [expanded, setExpanded] = useState(true)
  if (!content) return null
  return (
    <div style={{
      background: '#0d1420', border: '1px solid #1a2740',
      borderRadius: 12, marginBottom: 16, overflow: 'hidden',
    }}>
      <button
        onClick={() => setExpanded(e => !e)}
        style={{
          width: '100%', padding: '14px 18px',
          display: 'flex', alignItems: 'center', gap: 10,
          background: 'none', border: 'none', cursor: 'pointer',
          borderBottom: expanded ? '1px solid #1a2740' : 'none',
        }}
      >
        <div style={{
          width: 30, height: 30, borderRadius: 6,
          background: `${color}22`, display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Icon size={15} color={color} />
        </div>
        <span style={{ color: '#e8f0fe', fontWeight: 600, fontSize: 14 }}>{title}</span>
        <ChevronRight
          size={14} color="#7a90b8" style={{ marginLeft: 'auto',
          transform: expanded ? 'rotate(90deg)' : 'none', transition: 'transform 0.2s' }}
        />
      </button>
      {expanded && (
        <div style={{ padding: '16px 18px' }}>
          <pre style={{
            color: '#b0c4de', fontSize: 13, lineHeight: 1.7,
            whiteSpace: 'pre-wrap', wordBreak: 'break-word',
            margin: 0, fontFamily: 'DM Sans, sans-serif',
          }}>
            {content}
          </pre>
        </div>
      )}
    </div>
  )
}

export default function Dashboard() {
  const [tab, setTab] = useState('run') // run | agents | logs | report
  const [formData, setFormData] = useState({
    company: 'FitAI India',
    product: 'AI-powered fitness app for workout tracking, nutrition coaching, and stress management',
    target_audience: 'Working professionals aged 25-40 in Tier 1 Indian cities (Mumbai, Delhi, Bangalore)',
    goals: 'Launch GTM strategy, achieve 10,000 users in 6 months, build sustainable growth',
    constraints: 'Bootstrap budget under ₹50L, team of 5 people',
  })
  const [runId, setRunId] = useState(null)
  const [runStatus, setRunStatus] = useState(null) // pending | running | completed | failed
  const [agentStates, setAgentStates] = useState({})
  const [logs, setLogs] = useState([])
  const [report, setReport] = useState(null)
  const [totalTokens, setTotalTokens] = useState(0)
  const [qaScore, setQaScore] = useState(null)
  const [error, setError] = useState(null)
  const [events, setEvents] = useState([])
  const logsEndRef = useRef(null)
  const eventSourceRef = useRef(null)

  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs])

  const addLog = useCallback((agent, level, msg, extra = {}) => {
    setLogs(prev => [...prev, {
      ts: new Date().toISOString(),
      agent: agent || 'system',
      level,
      msg,
      ...extra,
    }])
  }, [])

  const startRun = async () => {
    setError(null)
    setRunStatus('running')
    setAgentStates({})
    setLogs([])
    setReport(null)
    setQaScore(null)
    setEvents([])
    setTotalTokens(0)
    setTab('agents')

    addLog('Orchestrator', 'info', 'Starting multi-agent workflow...')

    try {
      const res = await fetch('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Failed to start run')
      }

      const data = await res.json()
      setRunId(data.run_id)
      addLog('Orchestrator', 'info', `Run started: ${data.run_id}`)

      // Connect to SSE stream
      connectToStream(data.run_id)

    } catch (e) {
      setError(e.message)
      setRunStatus('failed')
      addLog('system', 'error', e.message)
    }
  }

  const connectToStream = (id) => {
    if (eventSourceRef.current) eventSourceRef.current.close()

    const es = new EventSource(`/api/run/${id}/stream`)
    eventSourceRef.current = es

    const handleEvent = (type, rawData) => {
      try {
        const parsed = JSON.parse(rawData)
        const { data } = parsed

        setEvents(prev => [...prev, { type, ...parsed }])

        if (type === 'agent_start') {
          setAgentStates(prev => ({ ...prev, [data.agent]: { status: 'running' } }))
          addLog(data.agent, 'info', data.description || 'Starting...')
        }

        if (type === 'agent_complete') {
          setAgentStates(prev => ({
            ...prev,
            [data.agent]: {
              status: 'completed',
              latency: data.latency_ms,
              tokens: data.tokens_used,
              model: data.model,
            }
          }))
          setTotalTokens(prev => prev + (data.tokens_used || 0))
          addLog(data.agent, 'info', `Completed in ${data.latency_ms}ms — ${data.tokens_used} tokens`)
        }

        if (type === 'agent_error') {
          setAgentStates(prev => ({
            ...prev, [data.agent]: { status: 'failed', error: data.error }
          }))
          addLog(data.agent, 'error', data.error)
        }

        if (type === 'workflow_complete') {
          setRunStatus('completed')
          setQaScore(data.qa_score)
          addLog('Orchestrator', 'info', `Workflow complete — QA Score: ${data.qa_score}/100`)
          addLog('Orchestrator', 'info', `Total tokens used: ${data.total_tokens}`)
          // Fetch full report
          fetchReport(id)
          es.close()
        }

        if (type === 'workflow_error') {
          setRunStatus('failed')
          setError(data.error)
          addLog('system', 'error', data.error)
          es.close()
        }

      } catch (e) { /* ignore parse errors */ }
    }

    // Register event types
    const eventTypes = ['agent_start', 'agent_complete', 'agent_error', 'workflow_complete', 'workflow_error', 'ping', 'done']
    eventTypes.forEach(type => {
      es.addEventListener(type, (e) => handleEvent(type, e.data))
    })

    es.onerror = () => {
      addLog('system', 'warn', 'SSE connection interrupted, polling for status...')
      es.close()
      // Fallback: poll for completion
      setTimeout(() => pollStatus(id), 3000)
    }
  }

  const pollStatus = async (id) => {
    try {
      const res = await fetch(`/api/run/${id}`)
      const data = await res.json()
      if (data.status === 'completed') {
        setRunStatus('completed')
        fetchReport(id)
      } else if (data.status === 'failed') {
        setRunStatus('failed')
      } else {
        setTimeout(() => pollStatus(id), 3000)
      }
    } catch (e) {}
  }

  const fetchReport = async (id) => {
    try {
      const res = await fetch(`/api/run/${id}`)
      const data = await res.json()
      if (data.final_report) {
        setReport(data.final_report)
        setQaScore(data.final_report.qa_score)
        setTotalTokens(data.final_report.token_usage?.total_tokens_used || totalTokens)
        setTab('report')
        addLog('system', 'info', 'Report ready — switching to Report tab')
      }
    } catch (e) {}
  }

  const getAgentState = (agentKey) => agentStates[agentKey] || {}

  const completedCount = Object.values(agentStates).filter(s => s.status === 'completed').length
  const progress = Math.round((completedCount / 5) * 100)

  return (
    <div style={{ minHeight: '100vh', background: '#080c12', color: '#e8f0fe' }}>
      {/* Header */}
      <div style={{
        borderBottom: '1px solid #1a2740',
        padding: '0 24px',
        display: 'flex', alignItems: 'center', gap: 16,
        height: 60,
        background: '#0a0f1a',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: 'linear-gradient(135deg, #00d4ff33, #7c3aed33)',
            border: '1px solid #00d4ff44',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Brain size={16} color="#00d4ff" />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 15, fontFamily: 'Space Mono' }}>
              AI-BI Platform
            </div>
            <div style={{ fontSize: 10, color: '#7a90b8' }}>Multi-Agent Intelligence</div>
          </div>
        </div>

        {/* Status bar */}
        {runStatus && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginLeft: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              {runStatus === 'running' && <Loader2 size={14} color="#00d4ff" style={{ animation: 'spin 1s linear infinite' }} />}
              {runStatus === 'completed' && <Check size={14} color="#00e676" />}
              {runStatus === 'failed' && <X size={14} color="#ff4444" />}
              <span style={{
                fontSize: 12, fontFamily: 'Space Mono',
                color: runStatus === 'running' ? '#00d4ff' : runStatus === 'completed' ? '#00e676' : '#ff4444'
              }}>
                {runStatus === 'running' ? `Running... ${progress}%` : runStatus === 'completed' ? 'Completed' : 'Failed'}
              </span>
            </div>

            {runStatus === 'running' && (
              <div style={{ width: 120, height: 4, background: '#1a2740', borderRadius: 2 }}>
                <div style={{
                  width: `${progress}%`, height: '100%',
                  background: 'linear-gradient(90deg, #00d4ff, #7c3aed)',
                  borderRadius: 2, transition: 'width 0.5s ease',
                }} />
              </div>
            )}

            {totalTokens > 0 && (
              <span style={{ fontSize: 11, color: '#7a90b8', fontFamily: 'Space Mono' }}>
                🔢 {totalTokens.toLocaleString()} tokens
              </span>
            )}

            {qaScore && (
              <span style={{
                fontSize: 11, fontFamily: 'Space Mono',
                color: qaScore >= 80 ? '#00e676' : qaScore >= 60 ? '#ffab00' : '#ff4444',
              }}>
                QA: {qaScore}/100
              </span>
            )}
          </div>
        )}

        {runId && (
          <div style={{ marginLeft: 'auto', fontSize: 11, color: '#334155', fontFamily: 'Space Mono' }}>
            RUN#{runId}
          </div>
        )}
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex', gap: 0,
        borderBottom: '1px solid #1a2740',
        padding: '0 24px',
        background: '#0a0f1a',
      }}>
        {[
          { id: 'run', label: 'New Run', icon: Play },
          { id: 'agents', label: 'Agent Timeline', icon: Activity },
          { id: 'logs', label: 'Logs', icon: Terminal },
          { id: 'report', label: 'Report', icon: FileText },
        ].map(t => {
          const Icon = t.icon
          const active = tab === t.id
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              style={{
                padding: '12px 20px',
                border: 'none', cursor: 'pointer',
                background: 'none',
                borderBottom: active ? '2px solid #00d4ff' : '2px solid transparent',
                color: active ? '#00d4ff' : '#7a90b8',
                fontSize: 13, fontWeight: 500,
                display: 'flex', alignItems: 'center', gap: 6,
                transition: 'color 0.2s',
              }}
            >
              <Icon size={14} />
              {t.label}
              {t.id === 'logs' && logs.length > 0 && (
                <span style={{
                  background: '#1a2740', color: '#7a90b8',
                  fontSize: 10, padding: '1px 5px', borderRadius: 8,
                  fontFamily: 'Space Mono',
                }}>
                  {logs.length}
                </span>
              )}
            </button>
          )
        })}
      </div>

      <div style={{ padding: 24, maxWidth: 1100, margin: '0 auto' }}>

        {/* NEW RUN TAB */}
        {tab === 'run' && (
          <div style={{ maxWidth: 720 }}>
            <div style={{ marginBottom: 24 }}>
              <h1 style={{ fontSize: 24, fontWeight: 700, margin: '0 0 6px', fontFamily: 'Space Mono' }}>
                Launch BI Analysis
              </h1>
              <p style={{ color: '#7a90b8', margin: 0, fontSize: 14 }}>
                6 specialized AI agents will autonomously research, strategize, critique, plan, and deliver your complete business intelligence report.
              </p>
            </div>

            {/* Architecture preview */}
            <div style={{
              background: '#0d1420', border: '1px solid #1a2740',
              borderRadius: 12, padding: 16, marginBottom: 24,
              display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center',
            }}>
              {AGENTS.filter(a => a.key !== 'orchestrator' && a.key !== 'memory').map((a, i) => {
                const Icon = a.icon
                return (
                  <div key={a.key} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <div style={{
                      display: 'flex', alignItems: 'center', gap: 5,
                      padding: '4px 10px', borderRadius: 6,
                      background: `${a.color}15`, border: `1px solid ${a.color}33`,
                    }}>
                      <Icon size={12} color={a.color} />
                      <span style={{ fontSize: 12, color: a.color }}>{a.name}</span>
                    </div>
                    {i < 4 && <ChevronRight size={12} color="#334155" />}
                  </div>
                )
              })}
            </div>

            {/* Form */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {[
                { key: 'company', label: 'Company Name', placeholder: 'e.g. FitAI India' },
                { key: 'product', label: 'Product Description', placeholder: 'What does your product do?', multiline: true },
                { key: 'target_audience', label: 'Target Audience', placeholder: 'Who are your customers?' },
                { key: 'goals', label: 'Business Goals', placeholder: 'What do you want to achieve?', multiline: true },
                { key: 'constraints', label: 'Constraints (optional)', placeholder: 'Budget, team size, timeline...' },
              ].map(field => (
                <div key={field.key}>
                  <label style={{ fontSize: 13, color: '#7a90b8', display: 'block', marginBottom: 6 }}>
                    {field.label}
                  </label>
                  {field.multiline ? (
                    <textarea
                      value={formData[field.key]}
                      onChange={e => setFormData(prev => ({ ...prev, [field.key]: e.target.value }))}
                      placeholder={field.placeholder}
                      rows={3}
                      style={{
                        width: '100%', background: '#0d1420',
                        border: '1px solid #1a2740', borderRadius: 8,
                        padding: '10px 14px', color: '#e8f0fe', fontSize: 14,
                        resize: 'vertical', fontFamily: 'DM Sans',
                        outline: 'none',
                      }}
                    />
                  ) : (
                    <input
                      value={formData[field.key]}
                      onChange={e => setFormData(prev => ({ ...prev, [field.key]: e.target.value }))}
                      placeholder={field.placeholder}
                      style={{
                        width: '100%', background: '#0d1420',
                        border: '1px solid #1a2740', borderRadius: 8,
                        padding: '10px 14px', color: '#e8f0fe', fontSize: 14,
                        fontFamily: 'DM Sans', outline: 'none',
                      }}
                    />
                  )}
                </div>
              ))}
            </div>

            {error && (
              <div style={{
                marginTop: 16, padding: '12px 16px',
                background: '#ff444418', border: '1px solid #ff444444',
                borderRadius: 8, color: '#ff6666', fontSize: 13,
                display: 'flex', gap: 8, alignItems: 'flex-start',
              }}>
                <AlertCircle size={14} style={{ flexShrink: 0, marginTop: 1 }} />
                {error}
              </div>
            )}

            <button
              onClick={startRun}
              disabled={runStatus === 'running'}
              style={{
                marginTop: 20,
                width: '100%', padding: '14px',
                background: runStatus === 'running'
                  ? '#1a2740'
                  : 'linear-gradient(135deg, #00d4ff22, #7c3aed22)',
                border: `1px solid ${runStatus === 'running' ? '#334155' : '#00d4ff44'}`,
                borderRadius: 10, cursor: runStatus === 'running' ? 'not-allowed' : 'pointer',
                color: runStatus === 'running' ? '#334155' : '#00d4ff',
                fontSize: 15, fontWeight: 600,
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                transition: 'all 0.2s',
              }}
            >
              {runStatus === 'running' ? (
                <><Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> Agents Working...</>
              ) : (
                <><Zap size={16} /> Launch Multi-Agent Analysis</>
              )}
            </button>

            <div style={{ marginTop: 12, fontSize: 12, color: '#334155', textAlign: 'center' }}>
              Free API • ChromaDB memory • ~5-8 minutes • Cost-protected
            </div>
          </div>
        )}

        {/* AGENTS TAB */}
        {tab === 'agents' && (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
              <div>
                <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700, fontFamily: 'Space Mono' }}>
                  Agent Execution Timeline
                </h2>
                <p style={{ margin: '4px 0 0', color: '#7a90b8', fontSize: 13 }}>
                  Real-time view of multi-agent collaboration
                </p>
              </div>
              {runStatus === 'completed' && (
                <div style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  padding: '6px 14px', borderRadius: 8,
                  background: '#00e67618', border: '1px solid #00e67644',
                  color: '#00e676', fontSize: 13, fontWeight: 600,
                }}>
                  <Check size={14} /> Workflow Complete
                </div>
              )}
            </div>

            {/* Model routing legend */}
            <div style={{
              background: '#0d1420', border: '1px solid #1a2740',
              borderRadius: 10, padding: '10px 16px', marginBottom: 20,
              display: 'flex', gap: 20, alignItems: 'center',
            }}>
              <span style={{ fontSize: 12, color: '#7a90b8' }}>LLM Routing:</span>
              <div style={{ display: 'flex', gap: 14 }}>
                {Object.entries(MODEL_COLORS).map(([m, c]) => (
                  <span key={m} style={{ fontSize: 12, color: c, fontFamily: 'Space Mono' }}>
                    ● {m.replace('llama-3.3-', '70b-').replace('llama-3.1-', '8b-')}
                  </span>
                ))}
              </div>
              {totalTokens > 0 && (
                <span style={{ marginLeft: 'auto', fontSize: 12, color: '#7a90b8', fontFamily: 'Space Mono' }}>
                  Total: {totalTokens.toLocaleString()} tokens
                </span>
              )}
            </div>

            {/* Agent cards grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
              {AGENTS.filter(a => a.key !== 'orchestrator' && a.key !== 'memory').map(agent => {
                const state = getAgentState(agent.key)
                return (
                  <AgentCard
                    key={agent.key}
                    agent={agent}
                    status={state.status}
                    latency={state.latency}
                    tokens={state.tokens}
                    model={state.model}
                    isActive={state.status === 'running'}
                  />
                )
              })}
            </div>

            {/* Memory agent */}
            <div style={{ marginTop: 12 }}>
              <AgentCard
                agent={AGENTS.find(a => a.key === 'memory')}
                status="completed"
                isActive={false}
              />
            </div>

            {/* Events feed */}
            {events.length > 0 && (
              <div style={{ marginTop: 20 }}>
                <div style={{ fontSize: 13, color: '#7a90b8', marginBottom: 10 }}>Event Stream</div>
                <div style={{
                  background: '#0d1420', border: '1px solid #1a2740',
                  borderRadius: 10, padding: 14, maxHeight: 200, overflow: 'auto',
                }}>
                  {events.slice(-20).map((e, i) => (
                    <div key={i} style={{
                      fontSize: 12, padding: '3px 0',
                      color: e.type === 'workflow_complete' ? '#00e676' :
                        e.type === 'agent_error' ? '#ff4444' : '#7a90b8',
                      fontFamily: 'Space Mono',
                    }}>
                      <span style={{ color: '#334155' }}>{e.timestamp?.slice(11, 19)} </span>
                      <span style={{ color: '#00d4ff' }}>[{e.type}] </span>
                      {e.data?.agent || e.data?.run_id || ''}
                      {e.data?.latency_ms ? ` — ${e.data.latency_ms}ms` : ''}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {!runId && (
              <div style={{
                marginTop: 40, textAlign: 'center',
                color: '#334155', fontSize: 14,
              }}>
                No active run. Go to <button
                  onClick={() => setTab('run')}
                  style={{ background: 'none', border: 'none', color: '#00d4ff', cursor: 'pointer', fontSize: 14 }}
                >New Run</button> to start.
              </div>
            )}
          </div>
        )}

        {/* LOGS TAB */}
        {tab === 'logs' && (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700, fontFamily: 'Space Mono' }}>
                Agent Logs
              </h2>
              <button
                onClick={() => setLogs([])}
                style={{
                  background: 'none', border: '1px solid #1a2740',
                  borderRadius: 6, padding: '5px 12px', color: '#7a90b8',
                  cursor: 'pointer', fontSize: 12, display: 'flex', alignItems: 'center', gap: 5,
                }}
              >
                <RefreshCw size={12} /> Clear
              </button>
            </div>

            <div style={{
              background: '#0d1420', border: '1px solid #1a2740',
              borderRadius: 12, padding: '14px 18px',
              minHeight: 400, maxHeight: '60vh', overflow: 'auto',
              fontFamily: 'Space Mono',
            }}>
              {logs.length === 0 ? (
                <div style={{ color: '#334155', fontSize: 13 }}>
                  No logs yet. Start a run to see agent activity.
                </div>
              ) : (
                <>
                  {logs.map((log, i) => <LogLine key={i} log={log} />)}
                  <div ref={logsEndRef} />
                </>
              )}
            </div>
          </div>
        )}

        {/* REPORT TAB */}
        {tab === 'report' && (
          <div>
            {!report ? (
              <div style={{ textAlign: 'center', padding: '60px 0', color: '#334155' }}>
                <FileText size={40} style={{ marginBottom: 16, opacity: 0.3 }} />
                <div style={{ fontSize: 14 }}>
                  {runStatus === 'running'
                    ? 'Report generating... agents are working'
                    : 'No report yet. Run an analysis first.'}
                </div>
              </div>
            ) : (
              <div>
                {/* Report header */}
                <div style={{
                  background: 'linear-gradient(135deg, #0d1420, #111c2e)',
                  border: '1px solid #1a2740', borderRadius: 12,
                  padding: 20, marginBottom: 20,
                }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
                    <div>
                      <div style={{ fontSize: 11, color: '#7a90b8', fontFamily: 'Space Mono', marginBottom: 4 }}>
                        BUSINESS INTELLIGENCE REPORT
                      </div>
                      <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700 }}>{report.company}</h1>
                      <div style={{ color: '#7a90b8', fontSize: 13, marginTop: 4 }}>{report.product?.slice(0, 80)}...</div>
                    </div>
                    <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                      <div style={{
                        padding: '10px 16px', borderRadius: 10,
                        background: report.qa_score >= 80 ? '#00e67618' : '#ffab0018',
                        border: `1px solid ${report.qa_score >= 80 ? '#00e67644' : '#ffab0044'}`,
                        textAlign: 'center',
                      }}>
                        <div style={{ fontSize: 24, fontWeight: 700, color: report.qa_score >= 80 ? '#00e676' : '#ffab00', fontFamily: 'Space Mono' }}>
                          {report.qa_score}
                        </div>
                        <div style={{ fontSize: 11, color: '#7a90b8' }}>QA Score</div>
                      </div>
                      <div style={{
                        padding: '10px 16px', borderRadius: 10,
                        background: '#00d4ff18', border: '1px solid #00d4ff33',
                        textAlign: 'center',
                      }}>
                        <div style={{ fontSize: 24, fontWeight: 700, color: '#00d4ff', fontFamily: 'Space Mono' }}>
                          {report.confidence_score || '—'}
                        </div>
                        <div style={{ fontSize: 11, color: '#7a90b8' }}>Confidence</div>
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: 12, marginTop: 16, flexWrap: 'wrap' }}>
                    <div style={{
                      padding: '5px 12px', borderRadius: 6, fontSize: 12,
                      background: report.verdict === 'APPROVED' ? '#00e67618' :
                        report.verdict === 'NEEDS REVISION' ? '#ff444418' : '#ffab0018',
                      color: report.verdict === 'APPROVED' ? '#00e676' :
                        report.verdict === 'NEEDS REVISION' ? '#ff6666' : '#ffab00',
                      border: '1px solid currentColor',
                    }}>
                      {report.verdict}
                    </div>
                    <span style={{ fontSize: 12, color: '#7a90b8' }}>
                      {report.sections_completed?.length || 0} sections • {report.token_usage?.total_tokens_used?.toLocaleString()} tokens used
                    </span>
                    <span style={{ fontSize: 12, color: '#334155' }}>
                      {new Date(report.generated_at).toLocaleString()}
                    </span>
                  </div>
                </div>

                {/* Report sections */}
                <ReportSection title="Market Research & Competitor Analysis" content={report.market_research} icon={Search} color="#00d4ff" />
                <ReportSection title="GTM & Business Strategy" content={report.strategy} icon={TrendingUp} color="#f59e0b" />
                <ReportSection title="Execution Plan (90-Day Roadmap)" content={report.execution_plan} icon={ListChecks} color="#10b981" />
                <ReportSection title="Critical Review & Assumptions Audit" content={report.critique} icon={AlertTriangle} color="#ef4444" />
                <ReportSection title="QA Validation & Scorecard" content={report.qa_report} icon={CheckCircle2} color="#ec4899" />
              </div>
            )}
          </div>
        )}
      </div>

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        @keyframes pulse-dot {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.4; transform: scale(0.8); }
        }
        input:focus, textarea:focus {
          border-color: #00d4ff44 !important;
          box-shadow: 0 0 0 3px #00d4ff11;
        }
      `}</style>
    </div>
  )
}
