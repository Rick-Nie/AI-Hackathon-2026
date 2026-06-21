import { UserPreferences, DietaryStyle, CuisineType } from '../types'
import { X, Search, MapPin } from 'lucide-react'
import { useState } from 'react'
import './PreferenceBuilder.css'

interface PreferenceBuilderProps {
  preferences: UserPreferences
  onPreferencesChange: (prefs: UserPreferences) => void
  onSearch: () => void
  loading: boolean
}

export default function PreferenceBuilder({
  preferences,
  onPreferencesChange,
  onSearch,
  loading,
}: PreferenceBuilderProps) {
  const [locating, setLocating] = useState(false)

  const handleGetLocation = async () => {
    setLocating(true)
    try {
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject)
      })

      const { latitude, longitude } = position.coords
      
      // Use OpenStreetMap's Nominatim reverse geocoding (free, no API key needed)
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`
      )
      const data = await response.json()
      
      // Extract city name
      const city = data.address?.city || 
                   data.address?.town || 
                   data.address?.county || 
                   `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`
      
      const updated = {
        ...preferences,
        location: city,
        latitude,
        longitude,
      }
      onPreferencesChange(updated)
    } catch (error) {
      console.error('Geolocation error:', error)
      alert('Could not get your location. Please enter it manually.')
    } finally {
      setLocating(false)
    }
  }

  const handleLocationChange = (newLocation: string) => {
    const updated = {
      ...preferences,
      location: newLocation,
      // clear precise coords if user types a generic city
      latitude: undefined,
      longitude: undefined,
    }
    onPreferencesChange(updated)
  }

  const removeAllergen = (allergen: string) => {
    const updated = {
      ...preferences,
      allergens: preferences.allergens.filter((a) => a !== allergen),
    }
    onPreferencesChange(updated)
  }

  const removeDietaryStyle = (style: DietaryStyle) => {
    const updated = {
      ...preferences,
      dietary_styles: preferences.dietary_styles.filter((s) => s !== style),
    }
    onPreferencesChange(updated)
  }

  const removeCuisine = (cuisine: CuisineType) => {
    const updated = {
      ...preferences,
      preferred_cuisines: preferences.preferred_cuisines.filter(
        (c) => c !== cuisine
      ),
    }
    onPreferencesChange(updated)
  }

  const removeLikedIngredient = (ingredient: string) => {
    const updated = {
      ...preferences,
      liked_ingredients: preferences.liked_ingredients.filter(
        (item) => item !== ingredient
      ),
    }
    onPreferencesChange(updated)
  }

  const removeDislikedIngredient = (ingredient: string) => {
    const updated = {
      ...preferences,
      disliked_ingredients: preferences.disliked_ingredients.filter(
        (item) => item !== ingredient
      ),
    }
    onPreferencesChange(updated)
  }

  const hasPreferences =
    preferences.allergens.length > 0 ||
    preferences.dietary_styles.length > 0 ||
    preferences.preferred_cuisines.length > 0 ||
    preferences.liked_ingredients.length > 0 ||
    preferences.disliked_ingredients.length > 0

  return (
    <div className="preference-builder">
      <h3>Your Preferences</h3>

      {!hasPreferences && (
        <p className="no-prefs-message">
          Talk to the chatbot to build your preferences...
        </p>
      )}

      {preferences.allergens.length > 0 && (
        <div className="pref-section">
          <label className="pref-label">🚫 Allergens</label>
          <div className="pref-tags">
            {preferences.allergens.map((allergen) => (
              <span key={allergen} className="pref-tag allergen-tag">
                <span>{allergen}</span>
                <button
                  onClick={() => removeAllergen(allergen)}
                  className="tag-remove"
                  title={`Remove ${allergen}`}
                >
                  <X size={14} />
                </button>
              </span>
            ))}
          </div>
        </div>
      )}

      {preferences.liked_ingredients.length > 0 && (
        <div className="pref-section">
          <label className="pref-label">👍 Likes</label>
          <div className="pref-tags">
            {preferences.liked_ingredients.map((ingredient) => (
              <span key={ingredient} className="pref-tag liked-tag">
                <span>{ingredient}</span>
                <button
                  onClick={() => removeLikedIngredient(ingredient)}
                  className="tag-remove"
                  title={`Remove ${ingredient}`}
                >
                  <X size={14} />
                </button>
              </span>
            ))}
          </div>
        </div>
      )}

      {preferences.disliked_ingredients.length > 0 && (
        <div className="pref-section">
          <label className="pref-label">👎 Dislikes</label>
          <div className="pref-tags">
            {preferences.disliked_ingredients.map((ingredient) => (
              <span key={ingredient} className="pref-tag dislike-tag">
                <span>{ingredient}</span>
                <button
                  onClick={() => removeDislikedIngredient(ingredient)}
                  className="tag-remove"
                  title={`Remove ${ingredient}`}
                >
                  <X size={14} />
                </button>
              </span>
            ))}
          </div>
        </div>
      )}

      {preferences.dietary_styles.length > 0 && (
        <div className="pref-section">
          <label className="pref-label">🥗 Diet</label>
          <div className="pref-tags">
            {preferences.dietary_styles.map((style) => (
              <span key={style} className="pref-tag diet-tag">
                <span>{style}</span>
                <button
                  onClick={() => removeDietaryStyle(style)}
                  className="tag-remove"
                  title={`Remove ${style}`}
                >
                  <X size={14} />
                </button>
              </span>
            ))}
          </div>
        </div>
      )}

          {preferences.preferred_cuisines.length > 0 && (
        <div className="pref-section">
          <label className="pref-label">🍜 Cuisines</label>
          <div className="pref-tags">
            {preferences.preferred_cuisines.map((cuisine) => (
              <span key={cuisine} className="pref-tag cuisine-tag">
                <span>{cuisine}</span>
                <button
                  onClick={() => removeCuisine(cuisine)}
                  className="tag-remove"
                  title={`Remove ${cuisine}`}
                >
                  <X size={14} />
                </button>
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="location-section">
        <label className="pref-label">📍 Location</label>
        <div className="location-input-group">
          <input
            type="text"
            placeholder="City or neighborhood"
            value={preferences.location || ''}
            onChange={(e) => handleLocationChange(e.target.value)}
            className="location-input"
          />
          <button
            onClick={handleGetLocation}
            disabled={locating}
            className="location-btn"
            title="Detect your current location"
          >
            <MapPin size={16} />
            {locating ? '...' : 'Use My Location'}
          </button>
        </div>
      </div>

      {hasPreferences && (
        <button
          className="search-btn"
          onClick={onSearch}
          disabled={loading}
        >
          <Search size={16} />
          {loading ? 'Searching...' : 'Search Restaurants'}
        </button>
      )}
    </div>
  )
}
