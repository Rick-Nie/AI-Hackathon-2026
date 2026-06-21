import { useState, useEffect } from 'react'
import './App.css'
import ChatInterface from './components/ChatInterface'
import PreferenceBuilder from './components/PreferenceBuilder'
import MapResults from './pages/MapResults'
import Sidebar from './components/Sidebar'
import LogoIcon from './components/LogoIcon'
import Reveal from './components/Reveal'
import Intro from './components/Intro'
import { useRestaurantSearch } from './hooks/useRestaurantSearch'
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
  const [introDone, setIntroDone] = useState(false)

  // Prefetches matched restaurants in the background whenever location or a
  // result-affecting preference changes, so opening Discover is instant.
  const search = useRestaurantSearch(preferences)

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

  const hasCoords = preferences.latitude !== undefined && preferences.longitude !== undefined

  return (
    <>
      {!introDone && <Intro onDone={() => setIntroDone(true)} />}
      <div className="app">
      <header className="masthead">
        <div className="masthead-inner">
          <a className="masthead-brand" href="#top" aria-label="DietMate67 home">
            <span className="masthead-logo"><LogoIcon /></span>
            <span className="masthead-words">
              <span className="eyebrow">Dietary Restaurant Matching</span>
              <span className="wordmark">DietMate<span className="wordmark-accent">67</span></span>
            </span>
          </a>

          <div className="masthead-meta">
            <span className="eyebrow">Vol.01 / &rsquo;26</span>
            <span className="masthead-rule" aria-hidden="true" />
            <span className="eyebrow masthead-coord">
              {hasCoords
                ? `${preferences.latitude!.toFixed(2)}°, ${preferences.longitude!.toFixed(2)}°`
                : 'Locating…'}
            </span>
          </div>
        </div>
      </header>

      <div className="shell" id="top">
        <Sidebar active={tab} setActive={setTab} />

        <div className="main-content">
          {tab === 'chat' && (
            <Reveal key="chat" className="chat-section">
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
            </Reveal>
          )}
          {tab === 'restaurants' && (
            <Reveal key="restaurants">
              <MapResults
                preferences={preferences}
                restaurants={search.restaurants}
                loading={search.loading}
                error={search.error}
                onLocationSaved={(lat, lon, label) =>
                  setPreferences((p) => ({ ...p, latitude: lat, longitude: lon, location: label }))
                }
              />
            </Reveal>
          )}
        </div>
      </div>
      </div>
    </>
  )
}

export default App
