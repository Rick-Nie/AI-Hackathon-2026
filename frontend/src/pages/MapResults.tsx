import { useEffect, useState, useRef, useCallback } from 'react'
import { GoogleMap, useJsApiLoader, Marker, InfoWindow } from '@react-google-maps/api'
import { api } from '../api'
import { UserPreferences, Restaurant } from '../types'
import { MapPin, Phone, Globe, Star, ChevronDown, ChevronUp } from 'lucide-react'
import './MapResults.css'

const GOOGLE_MAPS_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || ''

const MAP_CONTAINER_STYLE = { height: '100%', width: '100%' }

function scoreColor(score: number): string {
  if (score >= 75) return '#10b981'
  if (score >= 50) return '#f59e0b'
  if (score >= 30) return '#f97316'
  return '#ef4444'
}

function dietBadge(r: Restaurant, prefs: UserPreferences): { label: string; cls: string; note: string } {
  // If Claude gave us an AI note, use it for the note
  const aiNote = r.ai_dietary_note || ''

  const hasPrefs = prefs.allergens.length > 0 || prefs.dietary_styles.length > 0
  if (!hasPrefs) return { label: 'No filters set', cls: 'gray', note: 'Add dietary preferences to see compatibility' }

  // Lightweight cuisine-based heuristic for badge colour
  const text = (r.cuisine_types || []).join(' ').toLowerCase()
  const issues: string[] = []
  for (const style of prefs.dietary_styles) {
    const s = style.toLowerCase()
    if ((s === 'vegan' || s === 'vegetarian') && /burger|bbq|steak|grill|chicken|seafood|sushi|meat|fish/.test(text)) {
      issues.push(style)
    }
    if (s === 'halal' && /pork|bar|pub/.test(text)) issues.push(style)
    if (s === 'kosher' && /pork|shellfish|seafood/.test(text)) issues.push(style)
  }

  if (prefs.allergens.length > 0) {
    return { label: 'Verify allergens', cls: 'yellow', note: aiNote || `Call ahead — you're allergic to: ${prefs.allergens.join(', ')}` }
  }
  if (issues.length > 0) {
    return { label: 'May not fit diet', cls: 'yellow', note: aiNote || `Cuisine may conflict with: ${issues.join(', ')}` }
  }
  return { label: 'Likely compatible', cls: 'green', note: aiNote || 'Cuisine type looks suitable — verify menu to be sure' }
}

function markerUrl(score: number, selected: boolean): string {
  const color = selected ? '#7c3aed' : scoreColor(score)
  const r = selected ? 12 : 9
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${r*2+4}" height="${r*2+4}">
    <circle cx="${r+2}" cy="${r+2}" r="${r}" fill="${color}" stroke="white" stroke-width="2.5"/>
  </svg>`
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`
}

interface Props {
  preferences: UserPreferences
  onLocationSaved?: (lat: number, lon: number, label: string) => void
}

export default function MapResults({ preferences, onLocationSaved }: Props) {
  const { isLoaded, loadError } = useJsApiLoader({ googleMapsApiKey: GOOGLE_MAPS_KEY })

  const [restaurants, setRestaurants] = useState<Restaurant[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [locating, setLocating] = useState(false)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [infoOpen, setInfoOpen] = useState<string | null>(null)
  const [expandedReviews, setExpandedReviews] = useState<Set<string>>(new Set())
  const [mapRef, setMapRef] = useState<google.maps.Map | null>(null)
  const [activeFoodFilters, setActiveFoodFilters] = useState<Set<string>>(new Set())
  const [compatibleOnly, setCompatibleOnly] = useState(false)
  const cardRefs = useRef<Record<string, HTMLDivElement | null>>({})

  const hasLocation = preferences.latitude !== undefined && preferences.longitude !== undefined
  const userCenter = hasLocation
    ? { lat: preferences.latitude!, lng: preferences.longitude! }
    : { lat: 37.7749, lng: -122.4194 }

  useEffect(() => {
    if (!hasLocation) return
    let cancelled = false
    const load = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await api.searchRestaurantsGoogle({
          preferences,
          latitude: preferences.latitude!,
          longitude: preferences.longitude!,
          radius_meters: 2000,
          limit: 30,
        })
        if (!cancelled) setRestaurants(res.restaurants)
      } catch {
        if (!cancelled) setError('Could not load restaurants from Google Places.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [preferences.latitude, preferences.longitude])

  const handleSaveLocation = async () => {
    if (!('geolocation' in navigator)) { setError('Geolocation not supported.'); return }
    setLocating(true); setError(null)
    try {
      const pos = await new Promise<GeolocationPosition>((res, rej) =>
        navigator.geolocation.getCurrentPosition(res, rej, { enableHighAccuracy: true, timeout: 10000 })
      )
      const { latitude, longitude } = pos.coords
      let label = `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`
      try {
        const r = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`)
        const d = await r.json()
        label = d.address?.city || d.address?.town || d.address?.county || label
      } catch {}
      onLocationSaved?.(latitude, longitude, label)
    } catch { setError('Could not get location. Check browser permissions.') }
    finally { setLocating(false) }
  }

  const selectRestaurant = useCallback((r: Restaurant) => {
    setSelectedId(r.yelp_id)
    setInfoOpen(r.yelp_id)
    if (r.latitude && r.longitude && mapRef) {
      mapRef.panTo({ lat: r.latitude, lng: r.longitude })
      mapRef.setZoom(17)
    }
    cardRefs.current[r.yelp_id]?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }, [mapRef])

  const toggleReviews = (id: string) => {
    setExpandedReviews(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  // Build tag frequency map across all restaurants, sorted by count desc
  const tagFrequency = new Map<string, number>()
  for (const r of restaurants) {
    for (const ft of r.food_types ?? []) {
      const key = ft.toLowerCase()
      tagFrequency.set(key, (tagFrequency.get(key) ?? 0) + 1)
    }
  }
  const topTags = Array.from(tagFrequency.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 15)
    .map(([tag, count]) => ({ tag, count }))

  // Apply filters
  const visibleRestaurants = restaurants.filter((r) => {
    if (compatibleOnly && r.fits_diet === false) return false
    if (activeFoodFilters.size === 0) return true
    const foodSet = new Set((r.food_types ?? []).map((f) => f.toLowerCase()))
    return [...activeFoodFilters].some((f) => foodSet.has(f.toLowerCase()))
  })

  const toggleFoodFilter = (ft: string) => {
    setActiveFoodFilters((prev) => {
      const next = new Set(prev)
      next.has(ft) ? next.delete(ft) : next.add(ft)
      return next
    })
  }

  if (!hasLocation) {
    return (
      <div className="mr-placeholder">
        <div className="mr-placeholder-card">
          <div className="mr-placeholder-icon">📍</div>
          <h2>Save Your Location</h2>
          <p>Allow DietMate to detect your location and find nearby restaurants on Google Maps.</p>
          {error && <p className="mr-error-text">{error}</p>}
          <button className="mr-locate-btn" onClick={handleSaveLocation} disabled={locating}>
            {locating ? 'Detecting…' : 'Use My Location'}
          </button>
          <p className="mr-hint">Coordinates are stored locally only.</p>
        </div>
      </div>
    )
  }

  if (loadError) {
    return <div className="mr-placeholder"><div className="mr-placeholder-card"><p>Failed to load Google Maps. Check your API key.</p></div></div>
  }

  return (
    <div className="mr-layout">
      {/* ── LEFT: restaurant list ── */}
      <div className="mr-list">
        <div className="mr-list-header">
          <h2>
            {loading ? 'Loading restaurants…' : `${visibleRestaurants.length}${activeFoodFilters.size > 0 || compatibleOnly ? ` of ${restaurants.length}` : ''} Restaurants`}
          </h2>
          {preferences.location && <p className="mr-list-loc">📍 {preferences.location}</p>}
          {error && <p className="mr-error-text">{error}</p>}
          {loading && <div className="mr-spinner" />}

          {/* Filter bar — shown once restaurants load */}
          {!loading && restaurants.length > 0 && (
            <div className="mr-filter-bar">
              <button
                className={`mr-filter-chip mr-filter-chip--compat${compatibleOnly ? ' mr-filter-chip--active' : ''}`}
                onClick={() => setCompatibleOnly((v) => !v)}
              >
                ✅ Compatible only
              </button>
              {topTags.map(({ tag, count }) => (
                <button
                  key={tag}
                  className={`mr-filter-chip${activeFoodFilters.has(tag) ? ' mr-filter-chip--active' : ''}`}
                  onClick={() => toggleFoodFilter(tag)}
                  title={`${count} restaurant${count !== 1 ? 's' : ''} with "${tag}"`}
                >
                  {tag} <span className="mr-filter-count">{count}</span>
                </button>
              ))}
              {(activeFoodFilters.size > 0 || compatibleOnly) && (
                <button
                  className="mr-filter-chip mr-filter-chip--clear"
                  onClick={() => { setActiveFoodFilters(new Set()); setCompatibleOnly(false) }}
                >
                  ✕ Clear
                </button>
              )}
            </div>
          )}
        </div>

        <div className="mr-cards">
          {visibleRestaurants.map((r) => {
            const badge = dietBadge(r, preferences)
            const selected = r.yelp_id === selectedId
            const showReviews = expandedReviews.has(r.yelp_id)
            const hasReviews = (r.google_reviews?.length ?? 0) > 0

            return (
              <div
                key={r.yelp_id}
                ref={(el) => { cardRefs.current[r.yelp_id] = el }}
                className={`mr-card ${selected ? 'mr-card--selected' : ''}`}
                onClick={() => selectRestaurant(r)}
              >
                {/* header row */}
                <div className="mr-card-top">
                  <div>
                    <div className="mr-card-name">{r.name}</div>
                    {r.rating > 0 && (
                      <div className="mr-card-rating">
                        <Star size={12} fill="#fbbf24" color="#fbbf24" />
                        <span>{r.rating.toFixed(1)}</span>
                        <span className="mr-review-count">({r.review_count})</span>
                      </div>
                    )}
                  </div>
                  <div className="mr-score" style={{ background: scoreColor(r.match_score ?? 0) }}>
                    {Math.round(r.match_score ?? 0)}
                  </div>
                </div>

                {/* cuisine tags */}
                {r.cuisine_types.length > 0 && (
                  <div className="mr-cuisines">
                    {r.cuisine_types.slice(0, 4).map((c) => (
                      <span key={c} className="mr-cuisine-tag">{c}</span>
                    ))}
                  </div>
                )}

                {/* food type chips (extracted by AI from reviews) */}
                {(r.food_types ?? []).length > 0 && (
                  <div className="mr-food-types">
                    {(r.food_types!).slice(0, 8).map((ft) => (
                      <span key={ft} className="mr-food-tag">{ft}</span>
                    ))}
                  </div>
                )}

                {/* dietary badge */}
                <div className={`mr-diet-badge mr-diet-badge--${badge.cls}`}>
                  {badge.cls === 'green' ? '✅' : badge.cls === 'yellow' ? '⚠️' : badge.cls === 'red' ? '❌' : 'ℹ️'}{' '}
                  {badge.label}
                </div>

                {/* AI dietary note */}
                {badge.note && <div className="mr-diet-note">{badge.note}</div>}

                {/* Allergen / dislike warnings */}
                {(r.warnings ?? []).map((w, i) => (
                  <div key={i} className="mr-warning">{w}</div>
                ))}

                {/* contact / distance */}
                <div className="mr-card-meta">
                  {r.distance_miles !== undefined && (
                    <span><MapPin size={11} /> {r.distance_miles.toFixed(2)} mi</span>
                  )}
                  {r.phone && (
                    <a href={`tel:${r.phone}`} onClick={(e) => e.stopPropagation()}>
                      <Phone size={11} /> {r.phone}
                    </a>
                  )}
                  {r.url && (
                    <a href={r.url} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()}>
                      <Globe size={11} /> Website
                    </a>
                  )}
                </div>

                {r.address && <div className="mr-address">{r.address}</div>}

                {/* Google reviews toggle */}
                {hasReviews && (
                  <button
                    className="mr-reviews-toggle"
                    onClick={(e) => { e.stopPropagation(); toggleReviews(r.yelp_id) }}
                  >
                    {showReviews ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                    {showReviews ? 'Hide' : 'Show'} reviews ({r.google_reviews!.length})
                  </button>
                )}

                {showReviews && (
                  <div className="mr-reviews">
                    {(r.google_reviews || []).slice(0, 3).map((rv, i) => (
                      <div key={i} className="mr-review">
                        <div className="mr-review-header">
                          <strong>{rv.author_name}</strong>
                          <span className="mr-review-stars">{'★'.repeat(rv.rating)}{'☆'.repeat(5 - rv.rating)}</span>
                          <span className="mr-review-time">{rv.relative_time_description}</span>
                        </div>
                        <p className="mr-review-text">{rv.text}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* ── RIGHT: Google Map ── */}
      <div className="mr-map">
        {loadError ? (
          <div className="mr-map-loading">
            <p style={{ color: '#ef4444', textAlign: 'center', padding: '0 24px' }}>
              Google Maps failed to load.<br />
              <small style={{ color: '#9ca3af' }}>
                Check that Maps JavaScript API is enabled for your key.<br />
                Key used: {GOOGLE_MAPS_KEY ? `…${GOOGLE_MAPS_KEY.slice(-6)}` : '(none)'}
              </small>
            </p>
          </div>
        ) : isLoaded ? (
          <GoogleMap
            mapContainerStyle={MAP_CONTAINER_STYLE}
            center={userCenter}
            zoom={15}
            onLoad={(map) => setMapRef(map)}
            options={{ streetViewControl: false, mapTypeControl: false, fullscreenControl: true }}
          >
            {/* user location pin */}
            <Marker
              position={userCenter}
              title="You are here"
              icon={{
                url: `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(
                  '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28"><circle cx="14" cy="14" r="10" fill="#3b82f6" stroke="white" stroke-width="3"/><circle cx="14" cy="14" r="4" fill="white"/></svg>'
                )}`,
                anchor: new window.google.maps.Point(14, 14),
              }}
            />

            {/* restaurant markers */}
            {restaurants.map((r) =>
              r.latitude && r.longitude ? (
                <Marker
                  key={r.yelp_id}
                  position={{ lat: r.latitude, lng: r.longitude }}
                  title={r.name}
                  icon={{
                    url: markerUrl(r.match_score ?? 0, r.yelp_id === selectedId),
                    anchor: new window.google.maps.Point(11, 11),
                  }}
                  onClick={() => selectRestaurant(r)}
                >
                  {infoOpen === r.yelp_id && (
                    <InfoWindow onCloseClick={() => setInfoOpen(null)}>
                      <div className="mr-infowindow">
                        <strong>{r.name}</strong>
                        {r.rating > 0 && (
                          <div className="mr-iw-rating">
                            {'★'.repeat(Math.round(r.rating))} {r.rating.toFixed(1)} ({r.review_count})
                          </div>
                        )}
                        {r.address && <div className="mr-iw-addr">{r.address}</div>}
                        {r.cuisine_types.length > 0 && (
                          <div className="mr-iw-cuisine">{r.cuisine_types.slice(0, 3).join(', ')}</div>
                        )}
                        {r.ai_dietary_note && (
                          <div className="mr-iw-ai">{r.ai_dietary_note}</div>
                        )}
                        {r.url && (
                          <a href={r.url} target="_blank" rel="noopener noreferrer" className="mr-iw-link">
                            View website ↗
                          </a>
                        )}
                      </div>
                    </InfoWindow>
                  )}
                </Marker>
              ) : null
            )}
          </GoogleMap>
        ) : (
          <div className="mr-map-loading">
            <div className="mr-spinner" />
            <p>Loading Google Maps…</p>
          </div>
        )}

        {/* legend */}
        <div className="mr-legend">
          <span className="mr-legend-dot" style={{ background: '#3b82f6' }} /> You
          <span className="mr-legend-dot" style={{ background: '#10b981' }} /> High match
          <span className="mr-legend-dot" style={{ background: '#f59e0b' }} /> Medium
          <span className="mr-legend-dot" style={{ background: '#ef4444' }} /> Low
          <span className="mr-legend-dot" style={{ background: '#7c3aed' }} /> Selected
        </div>
      </div>
    </div>
  )
}
