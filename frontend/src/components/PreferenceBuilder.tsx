import { UserPreferences, DietaryStyle, CuisineType } from '../types'
import { X, Search } from 'lucide-react'
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

  const hasPreferences =
    preferences.allergens.length > 0 ||
    preferences.dietary_styles.length > 0 ||
    preferences.preferred_cuisines.length > 0

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
