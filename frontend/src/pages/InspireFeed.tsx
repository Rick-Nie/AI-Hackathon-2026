import { useState, useEffect, useRef, useCallback } from 'react'
import { api } from '../api'
import { FoodImage, UserPreferences } from '../types'
import './InspireFeed.css'

interface InspireFeedProps {
  preferences: UserPreferences
}

export default function InspireFeed({ preferences }: InspireFeedProps) {
  const [images, setImages] = useState<FoodImage[]>([])
  const [page, setPage] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const loaderRef = useRef<HTMLDivElement>(null)
  const PAGE_SIZE = 12

  const fetchPage = useCallback(async (pageNum: number, reset = false) => {
    if (loading) return
    setLoading(true)
    setError(null)
    try {
      const data = await api.getInspireImages({
        liked_ingredients: preferences.liked_ingredients,
        disliked_ingredients: preferences.disliked_ingredients,
        dietary_styles: preferences.dietary_styles,
        allergens: preferences.allergens,
        page: pageNum,
        page_size: PAGE_SIZE,
      })
      setImages(prev => reset ? data.images : [...prev, ...data.images])
      setHasMore(data.has_more)
      setPage(pageNum)
    } catch {
      setError('Could not load images. Make sure the backend is running.')
    } finally {
      setLoading(false)
    }
  }, [preferences, loading])

  // Initial load + reload when preferences change
  useEffect(() => {
    setImages([])
    setPage(0)
    setHasMore(true)
    fetchPage(0, true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    preferences.liked_ingredients.join(','),
    preferences.disliked_ingredients.join(','),
    preferences.allergens.join(','),
    preferences.dietary_styles.join(','),
  ])

  // IntersectionObserver for infinite scroll
  useEffect(() => {
    const el = loaderRef.current
    if (!el) return
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && hasMore && !loading) {
          fetchPage(page + 1)
        }
      },
      { rootMargin: '300px' }
    )
    obs.observe(el)
    return () => obs.disconnect()
  }, [hasMore, loading, page, fetchPage])

  const hasPrefs =
    preferences.liked_ingredients.length > 0 ||
    preferences.disliked_ingredients.length > 0 ||
    preferences.allergens.length > 0

  return (
    <div className="inspire-feed">
      <div className="inspire-header">
        <h2>Food Inspiration</h2>
        {hasPrefs && (
          <div className="inspire-pref-tags">
            {preferences.liked_ingredients.map(i => (
              <span key={i} className="inspire-chip liked">✓ {i}</span>
            ))}
            {preferences.disliked_ingredients.map(i => (
              <span key={i} className="inspire-chip disliked">✕ {i}</span>
            ))}
            {preferences.allergens.map(i => (
              <span key={i} className="inspire-chip allergen">⚠ {i}</span>
            ))}
          </div>
        )}
        {!hasPrefs && (
          <p className="inspire-hint">
            Set food preferences in the Chat or Preferences panel to personalize your feed.
          </p>
        )}
      </div>

      {error && <div className="inspire-error">{error}</div>}

      {images.length === 0 && !loading && !error && (
        <div className="inspire-empty">
          <span>🍽️</span>
          <p>No images match your current preferences. Try expanding your likes!</p>
        </div>
      )}

      <div className="inspire-masonry">
        {images.map(img => (
          <div
            key={img.id}
            className={`inspire-card ${expandedId === img.id ? 'expanded' : ''}`}
            onClick={() => setExpandedId(expandedId === img.id ? null : img.id)}
          >
            <div
              className="inspire-img-wrap"
              style={{ paddingBottom: `${(1 / img.aspect) * 100}%` }}
            >
              <img
                src={img.url}
                alt={img.title}
                loading="lazy"
                onError={(e) => {
                  (e.target as HTMLImageElement).src =
                    'https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=600&q=80'
                }}
              />
            </div>
            <div className="inspire-card-info">
              <p className="inspire-card-title">{img.title}</p>
              <div className="inspire-card-tags">
                {img.food_tags.slice(0, 4).map(tag => (
                  <span key={tag} className="inspire-tag">{tag}</span>
                ))}
              </div>
              {expandedId === img.id && (
                <p className="inspire-style-badge">{img.style}</p>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Infinite scroll sentinel */}
      <div ref={loaderRef} className="inspire-loader">
        {loading && (
          <div className="inspire-spinner">
            <span /><span /><span />
          </div>
        )}
        {!hasMore && images.length > 0 && (
          <p className="inspire-end">You've seen everything — update your preferences for a fresh feed!</p>
        )}
      </div>
    </div>
  )
}
