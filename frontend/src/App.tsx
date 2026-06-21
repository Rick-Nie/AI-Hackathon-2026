import { useState, useEffect } from 'react'
import './App.css'
import ChatInterface from './components/ChatInterface'
import PreferenceBuilder from './components/PreferenceBuilder'
import MapResults from './pages/MapResults'
import Sidebar from './components/Sidebar'
import { UserPreferences, SpiceLevel } from './types'
import { Utensils } from 'lucide-react'

const DEFAULT_PREFERENCES: UserPreferences = {
  dietary_styles: [],
  allergens: [],
  liked_ingredients: [],
  disliked_ingredients: [],
  preferred_cuisines: [],
  disliked_cuisines: [],
  max_spice_level: SpiceLevel.MEDIUM,
  latitude: undefined,
  longitude: undefined,
  max_distance_miles: 5.0,
  min_rating: 3.5,
  requires_open_now: true,
}

function App() {
  const [preferences, setPreferences] = useState<UserPreferences>(DEFAULT_PREFERENCES)
  const [tab, setTab] = useState<'chat' | 'restaurants'>('chat')

  const handlePreferencesUpdate = (updatedPrefs: UserPreferences) => {
    setPreferences(updatedPrefs)
  }

  // Auto-detect location on startup (browser caches permission — fast if already granted)
  useEffect(() => {
    if (!('geolocation' in navigator)) return
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude
        const lon = pos.coords.longitude
        setPreferences((p) => ({
          ...p,
          latitude: lat,
          longitude: lon,
          location: p.location || `${lat.toFixed(4)}, ${lon.toFixed(4)}`,
        }))
      },
      () => { /* permission denied — user can still click "Use My Location" in the map tab */ },
      { enableHighAccuracy: true, timeout: 10000 }
    )
  }, [])

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="logo">
            <Utensils size={32} />
            <h1>DietMate</h1>
            <p>Find restaurants that match YOUR dietary needs</p>
          </div>
        </div>
      </header>

      <div className="container with-sidebar">
        <Sidebar active={tab} setActive={(t) => setTab(t)} />

        <div className="main-content">
          {tab === 'chat' ? (
            <div className="chat-section">
              <ChatInterface
                preferences={preferences}
                onPreferencesUpdate={handlePreferencesUpdate}
                onSearch={() => setTab('restaurants')}
              />
              <PreferenceBuilder
                preferences={preferences}
                onPreferencesChange={handlePreferencesUpdate}
                onSearch={() => setTab('restaurants')}
                loading={false}
              />
            </div>
          ) : (
            <MapResults
              preferences={preferences}
              onLocationSaved={(lat, lon, label) =>
                setPreferences((p) => ({ ...p, latitude: lat, longitude: lon, location: label }))
              }
            />
          )}
        </div>
      </div>
    </div>
  )
}

export default App
