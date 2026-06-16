export default function StatCard({ label, value, hint, icon = '▣', tone = 'neutral' }) {
  return (
    <article className={`stat-card glass-card tone-${tone}`}>
      <div className="stat-card-head">
        <span className="stat-icon" aria-hidden="true">{icon}</span>
        <span>{label}</span>
      </div>
      <div className="stat-card-body">
        <strong>{value}</strong>
        <div className="mini-bars" aria-hidden="true">
          {Array.from({ length: 5 }).map((_, index) => (
            <i key={index} style={{ height: `${18 + index * 7}px` }} />
          ))}
        </div>
      </div>
      <small>{hint}</small>
    </article>
  );
}
