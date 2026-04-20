export default function ProviderCard({ provider }) {
  return (
    <div className="provider-card">
      <div className="card-header">
        <div className="card-title">
          <h3>{provider.name}</h3>
          {provider.specialty && (
            <span className="specialty">{provider.specialty}</span>
          )}
        </div>
        <div className="score-badge">
          <span className="score-value">{provider.rank_score.toFixed(1)}</span>
          <span className="score-label">Score</span>
        </div>
      </div>

      <div className="card-divider" />

      <div className="card-body">
        {(provider.city || provider.state) && (
          <p className="detail">
            <span className="detail-icon">📍</span>
            {[provider.city, provider.state].filter(Boolean).join(", ")}
            {provider.distance_miles != null &&
              ` · ${provider.distance_miles.toFixed(1)} mi away`}
          </p>
        )}
        {provider.phone && (
          <p className="detail">
            <span className="detail-icon">📞</span>
            {provider.phone}
          </p>
        )}
        {provider.insurance_accepted && (
          <p className="detail">
            <span className="detail-icon">🏥</span>
            {provider.insurance_accepted}
          </p>
        )}

        <div className="badges">
          {provider.telehealth && (
            <span className="badge telehealth">📱 Telehealth Available</span>
          )}
        </div>
      </div>
    </div>
  );
}
