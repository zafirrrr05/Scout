export default function UnknownUnknowns({ items, lang }) {
  if (!items || items.length === 0) return null

  return (
    <div className="unknown-unknowns-section">
      <div className="section-label">What you haven't asked yet</div>
      <div className="uu-hero-card">
        <div className="uu-header">
          <div className="uu-icon">💡</div>
          <div className="uu-header-text">
            <h3>Things you don't know you need to know</h3>
            <p>Surfaced from patterns across thousands of parenting journeys</p>
          </div>
        </div>
        <div className="uu-items">
          {items.map((item, i) => (
            <div key={i} className="uu-item">
              <div className="uu-insight">
                {lang === 'ar' && item.insight_ar ? item.insight_ar : item.insight}
              </div>
              {lang === 'ar' && item.insight_ar && (
                <div className="uu-insight-ar" dir="rtl">{item.insight_ar}</div>
              )}
              <div className="uu-why">
                {lang === 'ar' && item.why_it_matters_ar
                  ? item.why_it_matters_ar
                  : item.why_it_matters}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
