export default function ProviderCard({ provider }) {
  return (
    <div className="provider-card">
      <div className="card-header">
        <div>
          <h3>{provider.name}</h3>
          {provider.specialty && (
            <span className="specialty">{provider.specialty}</span>
          )}
        </div>
        <div className="score" title="Burden-reduction score">
          {provider.rank_score.toFixed(1)}
        </div>
      </div>

      <div className="card-body">
        {(provider.city || provider.state) && (
          <p className="detail">
            📍 {[provider.city, provider.state].filter(Boolean).join(", ")}
            {provider.distance_miles != null &&
              ` · ${provider.distance_miles.toFixed(1)} mi`}
          </p>
        )}
        {provider.phone && (
          <p className="detail">📞 {provider.phone}</p>
        )}
        {provider.insurance_accepted && (
          <p className="detail">🏥 {provider.insurance_accepted}</p>
        )}
        {provider.telehealth && (
          <span className="badge telehealth">Telehealth Available</span>
        )}
      </div>
    </div>
  );
}
