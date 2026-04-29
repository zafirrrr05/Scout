import { useState, useCallback } from 'react'
import BriefView from './components/BriefView.jsx'
import EvalDashboard from './components/EvalDashboard.jsx'
import { runScout } from './api.js'
import './index.css'

const LOADING_STEPS = [
  'Understanding your situation…',
  'Mapping your parenting journey…',
  'Surfacing what you haven\'t thought of yet…',
  'Preparing your brief…',
]

const EXAMPLES_EN = [
  "I'm 28 weeks pregnant, first baby, small apartment in Dubai Marina",
  "Baby is 4 months old, going back to work next month in Abu Dhabi",
  "Twin pregnancy, 32 weeks, first time, villa in Riyadh",
  "My baby has a fever of 39 degrees, what medicine?",
]

const EXAMPLES_AR = [
  "أنا حامل في الأسبوع ٢٨، أول طفل، شقة صغيرة في دبي",
  "طفلي عمره ٤ أشهر وسأعود للعمل الشهر القادم في أبوظبي",
  "حمل توأم، ٣٢ أسبوعاً، أول مرة، فيلا في الرياض",
]

function Header({ lang, onLangChange, activeView, onViewChange }) {
  return (
    <header className="app-header">
      <div className="page-container">
        <div className="header-inner">
          <div className="logo-mark">
            <div className="logo-icon">S</div>
            <div>
              <div className="logo-text">SCOUT</div>
              <div className="logo-sub">by Mumzworld</div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div className="view-tabs">
              <button
                className={`view-tab ${activeView !== 'evals' ? 'active' : ''}`}
                onClick={() => onViewChange('input')}
              >Brief</button>
              <button
                className={`view-tab ${activeView === 'evals' ? 'active' : ''}`}
                onClick={() => onViewChange('evals')}
              >Evals</button>
            </div>
            <div className="lang-toggle">
              <button className={`lang-btn ${lang === 'en' ? 'active' : ''}`} onClick={() => onLangChange('en')}>EN</button>
              <button className={`lang-btn ${lang === 'ar' ? 'active' : ''}`} onClick={() => onLangChange('ar')}>AR</button>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}

function InputView({ lang, onSubmit, errorMsg }) {
  const [input, setInput] = useState('')
  const examples = lang === 'ar' ? EXAMPLES_AR : EXAMPLES_EN

  const handleSubmit = useCallback(() => {
    if (input.trim().length > 3) onSubmit(input.trim())
  }, [input, onSubmit])

  return (
    <div className="input-view">
      <div className="input-hero">
        <div className="input-hero-eyebrow">Situation-Aware Intelligence</div>
        <h1>Tell me about your<br /><em>situation</em>.</h1>
        <p>SCOUT maps where you are right now to where you're headed — surfacing what you need, what decisions are coming, and what you haven't thought to ask yet.</p>
      </div>
      {errorMsg && (
        <div style={{ maxWidth: 680, width: '100%', marginBottom: 16, padding: '12px 20px', background: 'var(--red-crit-bg)', border: '1px solid rgba(220,38,38,0.2)', borderRadius: 12, color: '#991b1b', fontSize: 14 }}>
          ⚠️ {errorMsg}
        </div>
      )}
      <div className="input-card">
        <label className="input-label">{lang === 'ar' ? 'صفي وضعك' : 'Describe your situation'}</label>
        <textarea
          className="input-textarea"
          dir={lang === 'ar' ? 'rtl' : 'ltr'}
          placeholder={lang === 'ar' ? 'مثال: أنا حامل في الأسبوع ٢٨، أول طفل، أسكن في شقة في دبي...' : "e.g. I'm 28 weeks pregnant with my first baby, living in Dubai Marina..."}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleSubmit() }}
          maxLength={500}
          autoFocus
        />
        <div className="example-chips">
          {examples.map((ex, i) => (
            <button key={i} className="chip" onClick={() => setInput(ex)}>
              {ex.length > 52 ? ex.slice(0, 52) + '…' : ex}
            </button>
          ))}
        </div>
        <div className="submit-row">
          <span className="char-count">{input.length}/500 · ⌘↵ to submit</span>
          <button className="submit-btn" onClick={handleSubmit} disabled={input.trim().length < 4}>
            <span>Scout my journey</span><span>→</span>
          </button>
        </div>
      </div>
    </div>
  )
}

function LoadingView({ stepIndex }) {
  return (
    <div className="loading-view">
      <div className="loading-orb" />
      <div className="loading-step">{LOADING_STEPS[stepIndex % LOADING_STEPS.length]}</div>
      <div className="loading-dots"><span /><span /><span /></div>
    </div>
  )
}

function ClarifyView({ question, lang, onAnswer, onBack }) {
  const [answer, setAnswer] = useState('')
  return (
    <div className="input-view">
      <div className="clarify-card">
        <div className="clarify-icon">🤔</div>
        <h2>One quick question</h2>
        <p className="clarify-question">{question}</p>
        <textarea
          className="input-textarea"
          dir={lang === 'ar' ? 'rtl' : 'ltr'}
          placeholder={lang === 'ar' ? 'اكتبي إجابتك هنا...' : 'Type your answer here…'}
          value={answer}
          onChange={e => setAnswer(e.target.value)}
          style={{ minHeight: 80, marginBottom: 16 }}
          autoFocus
        />
        <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
          <button className="submit-btn" style={{ background: 'var(--ink-muted)', boxShadow: 'none' }} onClick={onBack}>← Back</button>
          <button className="submit-btn" disabled={answer.trim().length < 2} onClick={() => onAnswer(answer.trim())}>Continue →</button>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const [view, setView] = useState('input')
  const [lang, setLang] = useState('en')
  const [brief, setBrief] = useState(null)
  const [loadingStep, setLoadingStep] = useState(0)
  const [clarifyQuestion, setClarifyQuestion] = useState(null)
  const [originalInput, setOriginalInput] = useState('')
  const [error, setError] = useState(null)

  const handleSubmit = useCallback(async (inputText) => {
    setOriginalInput(inputText)
    setView('loading')
    setError(null)
    setBrief(null)
    const stepInterval = setInterval(() => setLoadingStep(s => (s + 1) % LOADING_STEPS.length), 2200)
    try {
      const result = await runScout(inputText, lang)
      setBrief(result)
      setView('brief')
    } catch (err) {
      if (err.status === 400 && err.clarifyingQuestion) {
        setClarifyQuestion(err.clarifyingQuestion)
        setView('clarify')
      } else {
        setError(err.message || 'Something went wrong. Please try again.')
        setView('input')
      }
    } finally {
      clearInterval(stepInterval)
      setLoadingStep(0)
    }
  }, [lang])

  const handleClarifyAnswer = useCallback((answer) => {
    handleSubmit(`${originalInput}. ${answer}`)
    setClarifyQuestion(null)
  }, [originalInput, handleSubmit])

  const handleBack = useCallback(() => {
    setBrief(null)
    setView('input')
    setError(null)
  }, [])

  const handleViewChange = useCallback((newView) => {
    if (newView === 'input') {
      setView(brief ? 'brief' : 'input')
    } else {
      setView(newView)
    }
  }, [brief])

  return (
    <div className="app-shell">
      <Header lang={lang} onLangChange={setLang} activeView={view} onViewChange={handleViewChange} />
      {view === 'input' && <InputView lang={lang} onSubmit={handleSubmit} errorMsg={error} />}
      {view === 'loading' && <LoadingView stepIndex={loadingStep} />}
      {view === 'clarify' && clarifyQuestion && (
        <ClarifyView question={clarifyQuestion} lang={lang} onAnswer={handleClarifyAnswer} onBack={handleBack} />
      )}
      {view === 'brief' && brief && (
        <div className="page-container">
          <BriefView brief={brief} lang={lang} onBack={handleBack} />
        </div>
      )}
      {view === 'evals' && (
        <div className="page-container">
          <EvalDashboard />
        </div>
      )}
    </div>
  )
}
