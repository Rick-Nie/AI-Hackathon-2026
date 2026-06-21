import { useState, useEffect } from 'react'
import './App.css'
import ChatInterface from './components/ChatInterface'
import PreferenceBuilder from './components/PreferenceBuilder'
import MapResults from './pages/MapResults'
import Sidebar from './components/Sidebar'
import LogoIcon from './components/LogoIcon'
import { UserPreferences, SpiceLevel } from './types'

const PREFS_STORAGE_KEY = 'dietmate_preferences'

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

function loadPreferences(): UserPreferences {
  try {
    const raw = localStorage.getItem(PREFS_STORAGE_KEY)
    if (raw) return { ...DEFAULT_PREFERENCES, ...JSON.parse(raw) }
  } catch {}
  return DEFAULT_PREFERENCES
}

type Tab = 'chat' | 'restaurants'

function App() {
  const [preferences, setPreferences] = useState<UserPreferences>(loadPreferences)
  const [tab, setTab] = useState<Tab>('chat')

  useEffect(() => {
    localStorage.setItem(PREFS_STORAGE_KEY, JSON.stringify(preferences))
  }, [preferences])

  const handlePreferencesUpdate = (updatedPrefs: UserPreferences) => {
    setPreferences(updatedPrefs)
  }

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
      () => {},
      { enableHighAccuracy: true, timeout: 10000 }
    )
  }, [])

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="logo">
            <LogoIcon />
            <h1>DietMate67</h1>
            <p>Find restaurants that match YOUR dietary needs</p>
          </div>
        </div>
      </header>

      <div className="container with-sidebar">
        <Sidebar active={tab} setActive={setTab} />

        <div className="main-content">
          {tab === 'chat' && (
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
          )}
          {tab === 'restaurants' && (
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
