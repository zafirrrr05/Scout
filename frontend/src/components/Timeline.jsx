export default function Timeline({ horizon, lang }) {
  if (!horizon || horizon.length === 0) {
    return <div className="empty-state">No upcoming stages found.</div>
  }

  const certaintyLabel = {
    will_happen: 'Certain',
    likely_happens: 'Likely',
    might_happen: 'Possible',
  }

  const certaintyClass = {
    will_happen: 'will',
    likely_happens: 'likely',
    might_happen: 'might',
  }

  return (
    <div className="timeline-strip">
      {horizon.map((item, i) => (
        <div
          key={item.node_id || i}
          className={`timeline-node certainty-${item.certainty}`}
          style={{ animationDelay: `${i * 0.08}s` }}
        >
          <div className="timeline-weeks">
            In {item.weeks_until} week{item.weeks_until !== 1 ? 's' : ''}
          </div>
          <div className="timeline-title">
            {lang === 'ar' && item.situation_ar ? item.situation_ar : item.situation}
          </div>
          <div className="timeline-preview">
            {lang === 'ar' && item.preview_ar ? item.preview_ar : item.preview}
          </div>
          <span className={`certainty-badge ${certaintyClass[item.certainty] || 'might'}`}>
            {certaintyLabel[item.certainty] || item.certainty}
          </span>
        </div>
      ))}
    </div>
  )
}
