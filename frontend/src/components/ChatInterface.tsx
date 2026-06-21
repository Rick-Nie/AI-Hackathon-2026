import { useState, useRef, useEffect } from 'react'
import { api } from '../api'
import { UserPreferences, ConversationMessage, ChatRequest } from '../types'
import { Send, Loader } from 'lucide-react'
import './ChatInterface.css'

interface ChatInterfaceProps {
  preferences: UserPreferences
  onPreferencesUpdate: (prefs: UserPreferences) => void
  onSearch: (prefs?: UserPreferences) => Promise<void>
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

    // Preserve the last chat request as search context
    const userSearchNotes = preferences.custom_notes
      ? `${preferences.custom_notes} ${userMessage}`
      : userMessage

    const requestPreferences = {
      ...preferences,
      custom_notes: userSearchNotes,
    }

    // Add user message to chat
    const updatedMessages: ConversationMessage[] = [
      ...messages,
      { role: 'user', content: userMessage },
    ]
    setMessages(updatedMessages)
    setLoading(true)

    try {
      const chatRequest: ChatRequest = {
        message: userMessage,
        conversation_history: updatedMessages,
        user_preferences: requestPreferences,
      }

      const response = await api.chat(chatRequest)

      const mergedPreferences = response.updated_preferences
        ? {
            ...requestPreferences,
            ...response.updated_preferences,
            custom_notes:
              response.updated_preferences.custom_notes ?? requestPreferences.custom_notes,
          }
        : requestPreferences

      onPreferencesUpdate(mergedPreferences)

      // Add assistant response
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: response.reply },
      ])

      // Store suggested searches
      setSuggestedSearches(response.suggested_searches)

      if (response.should_search) {
        await onSearch(mergedPreferences)
      }
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

  const handleSuggestedSearch = async (suggestion: string) => {
    if (suggestion.includes('Search restaurants')) {
      await onSearch()
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
