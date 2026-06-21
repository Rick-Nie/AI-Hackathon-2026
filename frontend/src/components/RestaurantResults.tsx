import { Restaurant, UserPreferences } from '../types'
import { Star, MapPin, Phone, Globe, AlertTriangle, Check } from 'lucide-react'
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
          <p>No restaurants found. Try adjusting your preferences.</p>
        </div>
      </div>
    )
  }

  const getRiskColor = (risk: string): string => {
    switch (risk.toUpperCase()) {
      case 'SAFE':
        return '#10b981'
      case 'LOW_RISK':
        return '#3b82f6'
      case 'MEDIUM_RISK':
        return '#f59e0b'
      case 'HIGH_RISK':
        return '#ef4444'
      default:
        return '#6b7280'
    }
  }

  return (
    <div className="restaurant-results">
      <div className="results-header">
        <h2>Found {restaurants.length} Restaurants</h2>
        <p className="results-summary">
          {preferences.location && `Near ${preferences.location}`}
        </p>
      </div>

      <div className="restaurants-grid">
        {restaurants.map((restaurant) => (
          <div key={restaurant.yelp_id} className="restaurant-card">
            <div className="card-header">
              <div>
                <h3>{restaurant.name}</h3>
                <div className="restaurant-meta">
                  <span className="rating">
                    <Star size={14} fill="currentColor" />
                    {restaurant.rating.toFixed(1)}
                  </span>
                  <span className="review-count">
                    ({restaurant.review_count} reviews)
                  </span>
                </div>
              </div>
              <div className="match-score">
                <div
                  className="score-badge"
                  style={{
                    background: `hsl(${(restaurant.match_score * 1.2) % 360}, 70%, 50%)`,
                  }}
                >
                  {Math.round(restaurant.match_score)}%
                </div>
                <span className="score-label">Match</span>
              </div>
            </div>

            <div className="cuisines">
              {restaurant.cuisines.map((cuisine) => (
                <span key={cuisine} className="cuisine-badge">
                  {cuisine}
                </span>
              ))}
            </div>

            <div className="allergen-section">
              <div
                className={`safety-indicator ${restaurant.allergen_report.is_safe ? 'safe' : 'warning'}`}
              >
                {restaurant.allergen_report.is_safe ? (
                  <>
                    <Check size={16} />
                    <span>Allergen Safe</span>
                  </>
                ) : (
                  <>
                    <AlertTriangle size={16} />
                    <span>Allergen Warning</span>
                  </>
                )}
              </div>
              <div className="safety-score">
                Safety Score:{' '}
                <strong style={{ color: getRiskColor(restaurant.allergen_report.overall_risk) }}>
                  {restaurant.allergen_report.safety_score}/100
                </strong>
              </div>
            </div>

            {restaurant.allergen_report.unsafe_items.length > 0 && (
              <div className="unsafe-items">
                <strong className="warning-label">⚠️ Avoid:</strong>
                <div className="items-list">
                  {restaurant.allergen_report.unsafe_items.slice(0, 3).map((item, idx) => (
                    <span key={idx} className="unsafe-item">
                      {item}
                    </span>
                  ))}
                  {restaurant.allergen_report.unsafe_items.length > 3 && (
                    <span className="more-items">
                      +{restaurant.allergen_report.unsafe_items.length - 3} more
                    </span>
                  )}
                </div>
              </div>
            )}

            {restaurant.recommended_dishes.length > 0 && (
              <div className="recommended-dishes">
                <strong className="dishes-label">✅ Recommended Dishes:</strong>
                <div className="dishes-list">
                  {restaurant.recommended_dishes.slice(0, 3).map((dish, idx) => (
                    <div key={idx} className="dish-item">
                      <span className="dish-name">{dish.name}</span>
                      {dish.price_usd && (
                        <span className="dish-price">${dish.price_usd.toFixed(2)}</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="restaurant-details">
              {restaurant.distance_miles !== undefined && (
                <div className="detail-item">
                  <MapPin size={14} />
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
                    View on Yelp
                  </a>
                </div>
              )}
            </div>

            <div className="card-status">
              {restaurant.is_open ? (
                <span className="open">🟢 Open Now</span>
              ) : (
                <span className="closed">🔴 Closed</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
