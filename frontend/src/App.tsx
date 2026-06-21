import { useState, useEffect } from 'react'
import './App.css'
import ChatInterface from './components/ChatInterface'
import RestaurantResults from './components/RestaurantResults'
import PreferenceBuilder from './components/PreferenceBuilder'
import { UserPreferences, SpiceLevel, Restaurant } from './types'
import { api } from './api'
import { MessageCircle, Utensils } from 'lucide-react'

const DEFAULT_PREFERENCES: UserPreferences = {
  dietary_styles: [],
  allergens: [],
  disliked_ingredients: [],
  preferred_cuisines: [],
  disliked_cuisines: [],
  max_spice_level: SpiceLevel.MEDIUM,
  max_distance_miles: 5.0,
  min_rating: 3.5,
  requires_open_now: true,
}

function App() {
  const [preferences, setPreferences] = useState<UserPreferences>(DEFAULT_PREFERENCES)
  const [restaurants, setRestaurants] = useState<Restaurant[]>([])
  const [loading, setLoading] = useState(false)
  const [tab, setTab] = useState<'chat' | 'results'>('chat')
  const [hasSearched, setHasSearched] = useState(false)

  const handlePreferencesUpdate = (updatedPrefs: UserPreferences) => {
    setPreferences(updatedPrefs)
  }

  const handleSearch = async () => {
    setLoading(true)
    try {
      const response = await api.searchRestaurants({
        preferences,
        limit: 10,
      })
      setRestaurants(response.restaurants)
      setHasSearched(true)
      setTab('results')
    } catch (error) {
      console.error('Search failed:', error)
    } finally {
      setLoading(false)
    }
  }

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

      <div className="container">
        <div className="tab-navigation">
          <button
            className={`tab-btn ${tab === 'chat' ? 'active' : ''}`}
            onClick={() => setTab('chat')}
          >
            <MessageCircle size={20} />
            Chat Assistant
          </button>
          {hasSearched && (
            <button
              className={`tab-btn ${tab === 'results' ? 'active' : ''}`}
              onClick={() => setTab('results')}
            >
              <Utensils size={20} />
              Restaurants ({restaurants.length})
            </button>
          )}
        </div>

        <div className="main-content">
          {tab === 'chat' ? (
            <div className="chat-section">
              <ChatInterface
                preferences={preferences}
                onPreferencesUpdate={handlePreferencesUpdate}
                onSearch={handleSearch}
              />
              <PreferenceBuilder
                preferences={preferences}
                onPreferencesChange={handlePreferencesUpdate}
                onSearch={handleSearch}
                loading={loading}
              />
            </div>
          ) : (
            <RestaurantResults
              restaurants={restaurants}
              preferences={preferences}
              loading={loading}
            />
          )}
        </div>
      </div>
    </div>
  )
}

export default App
