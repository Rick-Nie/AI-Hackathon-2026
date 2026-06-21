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
              <tag key={allergen} className="pref-tag allergen-tag">
                <span>{allergen}</span>
                <button
                  onClick={() => removeAllergen(allergen)}
                  className="tag-remove"
                  title={`Remove ${allergen}`}
                >
                  <X size={14} />
                </button>
              </tag>
            ))}
          </div>
        </div>
      )}

      {preferences.liked_ingredients.length > 0 && (
        <div className="pref-section">
          <label className="pref-label">👍 Likes</label>
          <div className="pref-tags">
            {preferences.liked_ingredients.map((ingredient) => (
              <tag key={ingredient} className="pref-tag liked-tag">
                <span>{ingredient}</span>
                <button
                  onClick={() => removeLikedIngredient(ingredient)}
                  className="tag-remove"
                  title={`Remove ${ingredient}`}
                >
                  <X size={14} />
                </button>
              </tag>
            ))}
          </div>
        </div>
      )}

      {preferences.disliked_ingredients.length > 0 && (
        <div className="pref-section">
          <label className="pref-label">👎 Dislikes</label>
          <div className="pref-tags">
            {preferences.disliked_ingredients.map((ingredient) => (
              <tag key={ingredient} className="pref-tag dislike-tag">
                <span>{ingredient}</span>
                <button
                  onClick={() => removeDislikedIngredient(ingredient)}
                  className="tag-remove"
                  title={`Remove ${ingredient}`}
                >
                  <X size={14} />
                </button>
              </tag>
            ))}
          </div>
        </div>
      )}

      {preferences.dietary_styles.length > 0 && (
        <div className="pref-section">
          <label className="pref-label">🥗 Diet</label>
          <div className="pref-tags">
            {preferences.dietary_styles.map((style) => (
              <tag key={style} className="pref-tag diet-tag">
                <span>{style}</span>
                <button
                  onClick={() => removeDietaryStyle(style)}
                  className="tag-remove"
                  title={`Remove ${style}`}
                >
                  <X size={14} />
                </button>
              </tag>
            ))}
          </div>
        </div>
      )}

          {preferences.preferred_cuisines.length > 0 && (
        <div className="pref-section">
          <label className="pref-label">🍜 Cuisines</label>
          <div className="pref-tags">
            {preferences.preferred_cuisines.map((cuisine) => (
              <tag key={cuisine} className="pref-tag cuisine-tag">
                <span>{cuisine}</span>
                <button
                  onClick={() => removeCuisine(cuisine)}
                  className="tag-remove"
                  title={`Remove ${cuisine}`}
                >
                  <X size={14} />
                </button>
              </tag>
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
