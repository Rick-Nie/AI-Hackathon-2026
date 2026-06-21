import { useState, useRef, useEffect } from 'react'
import { api } from '../api'
import { UserPreferences, ConversationMessage, ChatRequest } from '../types'
import { Send, Loader } from 'lucide-react'
import './ChatInterface.css'

interface ChatInterfaceProps {
  preferences: UserPreferences
  onPreferencesUpdate: (prefs: UserPreferences) => void
  onSearch: () => void
}

export default function ChatInterface({
  preferences,
  onPreferencesUpdate,
  onSearch,
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ConversationMessage[]>([
    {
      role: 'assistant',
      content:
        "Hi! I'm DietMate, your AI assistant for finding perfect restaurants. Tell me about your dietary preferences, allergies, or any dietary restrictions. I'll help you find restaurants that match your needs!",
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [suggestedSearches, setSuggestedSearches] = useState<string[]>([])
  const [lastExtractedPrefs, setLastExtractedPrefs] = useState<UserPreferences | null>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')

    // Add user message to chat
    const updatedMessages = [...messages, { role: 'user', content: userMessage }]
    setMessages(updatedMessages)
    setLoading(true)

    try {
      const chatRequest: ChatRequest = {
        message: userMessage,
        conversation_history: updatedMessages,
        user_preferences: preferences,
      }

      const response = await api.chat(chatRequest)

      // Update preferences if they were updated
      if (response.updated_preferences) {
        onPreferencesUpdate(response.updated_preferences)
        setLastExtractedPrefs(response.updated_preferences)
      }

      // Add assistant response
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: response.reply },
      ])

      // Store suggested searches
      setSuggestedSearches(response.suggested_searches)
    } catch (error) {
      console.error('Chat error:', error)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            "Sorry, I encountered an error. Please try again or use the preference builder on the right.",
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleSuggestedSearch = (suggestion: string) => {
    if (suggestion.includes('Search restaurants')) {
      onSearch()
    }
  }

  return (
    <div className="chat-interface">
      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message message-${msg.role}`}>
            <div className="message-avatar">
              {msg.role === 'user' ? '👤' : '🤖'}
            </div>
            <div className="message-content">
              <p>{msg.content}</p>
            </div>
          </div>
        ))}

        {lastExtractedPrefs && (
          <div className="message message-assistant prefs-summary">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <h4>Preferences I saved</h4>
              <div className="prefs-grid">
                {lastExtractedPrefs.liked_ingredients.length > 0 && (
                  <div>
                    <strong>Likes:</strong>
                    <div className="pref-tags">
                      {lastExtractedPrefs.liked_ingredients.map((i) => (
                        <span key={i} className="pref-chip liked-tag">{i}</span>
                      ))}
                    </div>
                  </div>
                )}
                {lastExtractedPrefs.disliked_ingredients.length > 0 && (
                  <div>
                    <strong>Dislikes:</strong>
                    <div className="pref-tags">
                      {lastExtractedPrefs.disliked_ingredients.map((i) => (
                        <span key={i} className="pref-chip dislike-tag">{i}</span>
                      ))}
                    </div>
                  </div>
                )}
                {lastExtractedPrefs.allergens.length > 0 && (
                  <div>
                    <strong>Allergens:</strong>
                    <div className="pref-tags">
                      {lastExtractedPrefs.allergens.map((a) => (
                        <span key={a} className="pref-chip allergen-tag">{a}</span>
                      ))}
                    </div>
                  </div>
                )}
                {lastExtractedPrefs.dietary_styles.length > 0 && (
                  <div>
                    <strong>Diet:</strong>
                    <div className="pref-tags">
                      {lastExtractedPrefs.dietary_styles.map((d) => (
                        <span key={d} className="pref-chip diet-tag">{d}</span>
                      ))}
                    </div>
                  </div>
                )}
                {lastExtractedPrefs.preferred_cuisines.length > 0 && (
                  <div>
                    <strong>Cuisines:</strong>
                    <div className="pref-tags">
                      {lastExtractedPrefs.preferred_cuisines.map((c) => (
                        <span key={c} className="pref-chip cuisine-tag">{c}</span>
                      ))}
                    </div>
                  </div>
                )}
                {lastExtractedPrefs.location && (
                  <div>
                    <strong>Location:</strong>
                    <div>{lastExtractedPrefs.location}</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
        {loading && (
          <div className="message message-assistant">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <div className="loading-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {suggestedSearches.length > 0 && (
        <div className="suggested-searches">
          <label>💡 Suggested:</label>
          <div className="search-buttons">
            {suggestedSearches.map((suggestion, idx) => (
              <button
                key={idx}
                className="suggestion-btn"
                onClick={() => handleSuggestedSearch(suggestion)}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      <form onSubmit={handleSendMessage} className="chat-input-form">
        <input
          type="text"
          placeholder="Tell me about your dietary preferences..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
          className="chat-input"
        />
        <button type="submit" disabled={loading} className="send-btn">
          {loading ? <Loader size={20} /> : <Send size={20} />}
        </button>
      </form>
    </div>
  )
}
