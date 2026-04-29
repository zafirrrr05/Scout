import Timeline from './Timeline.jsx'
import UnknownUnknowns from './UnknownUnknowns.jsx'

function UrgencyBadge({ urgency }) {
  const dot = { immediate: '🔴', soon: '🟠', upcoming: '🟢' }
  return (
    <span className={`urgency-badge ${urgency}`}>
      {dot[urgency] || '⚪'} {urgency}
    </span>
  )
}

export default function BriefView({ brief, lang, onBack }) {
  if (!brief) return null

  const hasRefusals = brief.out_of_scope_queries && brief.out_of_scope_queries.length > 0
  const hasSafety = brief.safety_flags && brief.safety_flags.length > 0
  const summaryText = lang === 'ar' && brief.current_situation_summary_ar
    ? brief.current_situation_summary_ar
    : brief.current_situation_summary

  return (
    <div className="brief-view">
      <button className="brief-back-btn" onClick={onBack}>
        ← New situation
      </button>

      {/* Safety flags — top priority */}
      {hasSafety && (
        <div className="safety-banner">
          <div className="safety-banner-title">⚠️ Safety Flags</div>
          {brief.safety_flags.map((sf, i) => (
            <div key={i} className="safety-flag-item">
              <span>{sf.severity === 'critical' ? '🚨' : '⚠️'}</span>
              <span><strong>{sf.product_name}</strong>: {sf.flag}</span>
            </div>
          ))}
        </div>
      )}

      {/* Refused medical queries */}
      {hasRefusals && (
        <div className="refusal-card">
          <div className="refusal-title">🩺 Outside SCOUT's scope</div>
          {brief.out_of_scope_queries.map((q, i) => (
            <div key={i} className="refusal-item">
              <strong>"{q}"</strong> — Please consult your pediatrician or OB.
            </div>
          ))}
        </div>
      )}

      {/* Header */}
      <div className="brief-header">
        <div className="brief-header-top">
          <div className="situation-badge">
            📍 Your Situation
          </div>
          <div className="confidence-pill">
            <span className="confidence-dot" />
            {Math.round((brief.confidence || 0.8) * 100)}% confident
          </div>
        </div>
        <div
          className="brief-summary"
          dir={lang === 'ar' ? 'rtl' : 'ltr'}
        >
          {summaryText}
        </div>
        {brief.processing_time_ms > 0 && (
          <div className="processing-time">
            Generated in {(brief.processing_time_ms / 1000).toFixed(1)}s
          </div>
        )}
      </div>

      {/* Timeline */}
      {brief.horizon && brief.horizon.length > 0 && (
        <div style={{ marginBottom: 40 }}>
          <div className="section-label">What's coming</div>
          <Timeline horizon={brief.horizon} lang={lang} />
        </div>
      )}

      {/* Unknown Unknowns — hero section */}
      {brief.unknown_unknowns && brief.unknown_unknowns.length > 0 && (
        <UnknownUnknowns items={brief.unknown_unknowns} lang={lang} />
      )}

      {/* Immediate Needs */}
      {brief.immediate_needs && brief.immediate_needs.length > 0 && (
        <div style={{ marginBottom: 40 }}>
          <div className="section-label">What you need now</div>
          <div className="products-grid">
            {brief.immediate_needs.map((product, i) => (
              <div key={product.id || i} className="product-card">
                <div className="product-urgency-row">
                  <UrgencyBadge urgency={product.urgency} />
                  <span className="product-price">AED {product.price_range_aed}</span>
                </div>
                <div className="product-name">
                  {lang === 'ar' && product.name_ar ? product.name_ar : product.name}
                </div>
                {lang === 'ar' && product.name_ar && product.name && (
                  <div className="product-name-ar" dir="rtl">{product.name_ar}</div>
                )}
                <div className="product-reason">
                  {lang === 'ar' && product.reason_ar ? product.reason_ar : product.reason}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Decisions */}
      {brief.decisions_coming && brief.decisions_coming.length > 0 && (
        <div style={{ marginBottom: 40 }}>
          <div className="section-label">Decisions coming</div>
          <div className="decisions-grid">
            {brief.decisions_coming.map((dec, i) => (
              <div key={i} className="decision-card">
                <div className="decision-deadline">
                  ⏱ Within {dec.deadline_weeks} week{dec.deadline_weeks !== 1 ? 's' : ''}
                </div>
                <div className="decision-title">
                  {lang === 'ar' && dec.title_ar ? dec.title_ar : dec.title}
                </div>
                <div className="decision-desc">
                  {lang === 'ar' && dec.description_ar ? dec.description_ar : dec.description}
                </div>
                <div className="decision-stakes">
                  {lang === 'ar' && dec.stakes_ar ? dec.stakes_ar : dec.stakes}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Hallucination warning (dev) */}
      {brief.hallucination_flags && brief.hallucination_flags.length > 0 && (
        <div style={{
          background: '#fff7ed', border: '1px solid #fed7aa',
          borderRadius: 12, padding: '12px 16px', fontSize: 12, color: '#9a3412'
        }}>
          ⚠️ <strong>Grounding flags:</strong> {brief.hallucination_flags.join(', ')}
        </div>
      )}
    </div>
  )
}
