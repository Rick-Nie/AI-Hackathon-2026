import { Restaurant, UserPreferences } from '../types'
import { MapPin, Phone, Globe, AlertTriangle, Check, ShieldCheck, Navigation } from 'lucide-react'
import './RestaurantResults.css'

interface RestaurantResultsProps {
  restaurants: Restaurant[]
  preferences: UserPreferences
  loading: boolean
}

export default function RestaurantResults({
  restaurants,
  preferences,
  loading,
}: RestaurantResultsProps) {
  if (loading) {
    return (
      <div className="restaurant-results">
        <div className="loading-message">
          <div className="spinner"></div>
          <p>Finding perfect restaurants for you...</p>
        </div>
      </div>
    )
  }

  if (restaurants.length === 0) {
    return (
      <div className="restaurant-results">
        <div className="empty-message">
          <p>No restaurants found. Try adjusting your preferences or expanding your search radius.</p>
        </div>
      </div>
    )
  }

  const getScoreColor = (score: number): string => {
    if (score >= 75) return '#10b981'
    if (score >= 50) return '#f59e0b'
    return '#ef4444'
  }

  const getSafetyLabel = (report?: Restaurant['allergen_safety']): string => {
    if (!report) return 'Not checked'
    if (report.safety_score >= 80) return 'High Safety'
    if (report.safety_score >= 60) return 'Moderate'
    return 'Low Safety'
  }

  return (
    <div className="restaurant-results">
      <div className="results-header">
        <h2>Found {restaurants.length} Restaurants</h2>
        {preferences.location && (
          <p className="results-summary">
            <Navigation size={14} /> Near {preferences.location}
          </p>
        )}
      </div>

      <div className="restaurants-grid">
        {restaurants.map((restaurant) => (
          <div key={restaurant.yelp_id} className="restaurant-card">

            {/* Header: name + match score */}
            <div className="card-header">
              <div>
                <h3>{restaurant.name}</h3>
                <div className="restaurant-meta">
                  {restaurant.price_range && (
                    <span className="price-range">{restaurant.price_range}</span>
                  )}
                  {restaurant.is_open_now !== undefined && (
                    <span className={restaurant.is_open_now ? 'open' : 'closed'}>
                      {restaurant.is_open_now ? '🟢 Open' : '🔴 Closed'}
                    </span>
                  )}
                </div>
              </div>
              <div className="match-score">
                <div
                  className="score-badge"
                  style={{ background: getScoreColor(restaurant.match_score) }}
                >
                  {Math.round(restaurant.match_score)}
                </div>
                <span className="score-label">Match</span>
              </div>
            </div>

            {/* Cuisine tags */}
            {restaurant.cuisine_types.length > 0 && (
              <div className="cuisines">
                {restaurant.cuisine_types.map((cuisine) => (
                  <span key={cuisine} className="cuisine-badge">{cuisine}</span>
                ))}
              </div>
            )}

            {/* Allergen safety */}
            {restaurant.allergen_safety && preferences.allergens.length > 0 && (
              <div className="allergen-section">
                <div className={`safety-indicator ${restaurant.allergen_safety.is_safe ? 'safe' : 'warning'}`}>
                  {restaurant.allergen_safety.is_safe ? (
                    <><ShieldCheck size={16} /><span>Allergen Safe</span></>
                  ) : (
                    <><AlertTriangle size={16} /><span>Allergen Warning</span></>
                  )}
                  <span className="safety-score-inline">
                    {restaurant.allergen_safety.safety_score}/100 · {getSafetyLabel(restaurant.allergen_safety)}
                  </span>
                </div>

                {restaurant.allergen_safety.unsafe_items.length > 0 && (
                  <div className="unsafe-items">
                    <strong className="warning-label">⚠️ Contains your allergens:</strong>
                    <div className="items-list">
                      {restaurant.allergen_safety.unsafe_items.slice(0, 3).map((item, idx) => (
                        <span key={idx} className="unsafe-item">{item}</span>
                      ))}
                      {restaurant.allergen_safety.unsafe_items.length > 3 && (
                        <span className="more-items">
                          +{restaurant.allergen_safety.unsafe_items.length - 3} more
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {restaurant.allergen_safety.high_risk_items.length > 0 && (
                  <div className="unsafe-items">
                    <strong className="warning-label" style={{ color: '#f59e0b' }}>
                      ⚠️ Cross-contamination risk:
                    </strong>
                    <div className="items-list">
                      {restaurant.allergen_safety.high_risk_items.slice(0, 2).map((item, idx) => (
                        <span key={idx} className="unsafe-item" style={{ borderColor: '#f59e0b', color: '#92400e' }}>
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Safe menu items */}
            {restaurant.safe_menu_items.length > 0 && (
              <div className="recommended-dishes">
                <strong className="dishes-label">
                  <Check size={14} /> Safe dishes for you:
                </strong>
                <div className="dishes-list">
                  {restaurant.safe_menu_items.slice(0, 4).map((dish, idx) => (
                    <div key={idx} className="dish-item">
                      <span className="dish-name">{dish.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Match reasons */}
            {restaurant.match_reasons.length > 0 && (
              <div className="match-reasons">
                {restaurant.match_reasons.map((reason, idx) => (
                  <span key={idx} className="reason-badge">{reason}</span>
                ))}
              </div>
            )}

            {/* Location + contact */}
            <div className="restaurant-details">
              <div className="detail-item">
                <MapPin size={14} />
                <span>{restaurant.address}</span>
              </div>
              {restaurant.distance_miles !== undefined && (
                <div className="detail-item">
                  <Navigation size={14} />
                  <span>{restaurant.distance_miles.toFixed(1)} mi away</span>
                </div>
              )}
              {restaurant.phone && (
                <div className="detail-item">
                  <Phone size={14} />
                  <a href={`tel:${restaurant.phone}`}>{restaurant.phone}</a>
                </div>
              )}
              {restaurant.url && (
                <div className="detail-item">
                  <Globe size={14} />
                  <a href={restaurant.url} target="_blank" rel="noopener noreferrer">
                    Website
                  </a>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
