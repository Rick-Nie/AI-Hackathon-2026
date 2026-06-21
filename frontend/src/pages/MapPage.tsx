import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, CircleMarker } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import { api } from '../api'
import { UserPreferences, Restaurant, MapSearchRequest } from '../types'
import './MapPage.css'

try {
  delete (L.Icon.Default.prototype as any)._getIconUrl
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: new URL('leaflet/dist/images/marker-icon-2x.png', import.meta.url).href,
    iconUrl: new URL('leaflet/dist/images/marker-icon.png', import.meta.url).href,
    shadowUrl: new URL('leaflet/dist/images/marker-shadow.png', import.meta.url).href,
  })
} catch (error) {
  // Ignore asset patch failures in environments where URL import isn't supported
}

interface MapPageProps {
  preferences: UserPreferences
  onLocationSaved?: (lat: number, lon: number, label: string) => void
}

export default function MapPage({ preferences, onLocationSaved }: MapPageProps) {
  const [restaurants, setRestaurants] = useState<Restaurant[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [locating, setLocating] = useState(false)

  const hasLocation = preferences.latitude !== undefined && preferences.longitude !== undefined

  const markerColor = (score?: number) => {
    if (score === undefined || score === null) return '#6b7280'
    if (score >= 75) return '#10b981'
    if (score >= 50) return '#f59e0b'
    if (score >= 30) return '#f97316'
    return '#ef4444'
  }

  const handleSaveLocation = async () => {
    if (!('geolocation' in navigator)) {
      setError('Geolocation is not supported by your browser.')
      return
    }
    setLocating(true)
    setError(null)
    try {
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, { enableHighAccuracy: true, timeout: 10000 })
      })
      const { latitude, longitude } = position.coords

      let label = `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`
      try {
        const res = await fetch(
          `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`
        )
        const data = await res.json()
        label = data.address?.city || data.address?.town || data.address?.county || label
      } catch {
        // keep coordinate fallback label
      }

      onLocationSaved?.(latitude, longitude, label)
    } catch (e) {
      setError('Could not get your location. Please allow location access in your browser.')
    } finally {
      setLocating(false)
    }
  }

  useEffect(() => {
    if (!hasLocation) return

    const fetchData = async () => {
      setLoading(true)
      setError(null)
      try {
        const req: MapSearchRequest = {
          preferences,
          latitude: preferences.latitude!,
          longitude: preferences.longitude!,
          radius_meters: 2000,
          limit: 50,
        }
        const res = await api.searchRestaurantsOsm(req)
        setRestaurants(res.restaurants)
      } catch (e) {
        console.error('OSM restaurant search failed', e)
        setError('Unable to load restaurants from the server.')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [preferences.latitude, preferences.longitude])

  if (!hasLocation) {
    return (
      <div className="map-placeholder">
        <div className="map-placeholder-card">
          <div className="map-placeholder-icon">📍</div>
          <h2>Save Your Location</h2>
          <p>
            Allow DietMate to use your location to find nearby restaurants that match
            your dietary preferences and restrictions.
          </p>
          {error && <p className="map-location-error">{error}</p>}
          <button
            className="map-location-btn"
            onClick={handleSaveLocation}
            disabled={locating}
          >
            {locating ? 'Detecting location…' : 'Save My Location & Find Restaurants'}
          </button>
          <p className="map-location-hint">
            Your coordinates are only stored locally and used to search nearby restaurants.
          </p>
        </div>
      </div>
    )
  }

  const userCenter = [preferences.latitude!, preferences.longitude!] as [number, number]

  return (
    <div className="map-page">
      {error && <div className="map-error-banner">{error}</div>}
      {loading && <div className="map-loading-banner">Loading nearby matches…</div>}
      <MapContainer center={userCenter} zoom={15} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        />
        <Marker position={userCenter}>
          <Popup>
            <strong>You are here</strong>
            {preferences.location && <div>{preferences.location}</div>}
          </Popup>
        </Marker>
        {restaurants.map((restaurant) =>
          restaurant.latitude && restaurant.longitude ? (
            <CircleMarker
              key={`${restaurant.name}-${restaurant.latitude}-${restaurant.longitude}`}
              center={[restaurant.latitude, restaurant.longitude]}
              radius={8}
              pathOptions={{ color: markerColor(restaurant.match_score), fillOpacity: 0.8 }}
            >
              <Popup>
                <div className="map-popup">
                  <strong>{restaurant.name}</strong>
                  {restaurant.address && <div className="map-popup-address">{restaurant.address}</div>}
                  <div className="map-popup-score">
                    Match score: <strong>{restaurant.match_score ?? 'N/A'}</strong>
                  </div>
                  {restaurant.warnings && restaurant.warnings.length > 0 && (
                    <div className="map-popup-warning">⚠️ {restaurant.warnings.join(' • ')}</div>
                  )}
                </div>
              </Popup>
            </CircleMarker>
          ) : null
        )}
      </MapContainer>
    </div>
  )
}
