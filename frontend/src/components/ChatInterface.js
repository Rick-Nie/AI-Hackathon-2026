import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useRef, useEffect } from 'react';
import { api } from '../api';
import { Send, Loader } from 'lucide-react';
import './ChatInterface.css';
export default function ChatInterface({ preferences, onPreferencesUpdate, onSearch, }) {
    const [messages, setMessages] = useState([
        {
            role: 'assistant',
            content: "Hi! I'm DietMate, your AI assistant for finding perfect restaurants. Tell me about your dietary preferences, allergies, or any dietary restrictions. I'll help you find restaurants that match your needs!",
        },
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);
    const [suggestedSearches, setSuggestedSearches] = useState([]);
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };
    useEffect(() => {
        scrollToBottom();
    }, [messages]);
    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading)
            return;
        const userMessage = input.trim();
        setInput('');
        // Preserve the last chat request as search context
        const userSearchNotes = preferences.custom_notes
            ? `${preferences.custom_notes} ${userMessage}`
            : userMessage;
        const requestPreferences = {
            ...preferences,
            custom_notes: userSearchNotes,
        };
        // Add user message to chat
        const updatedMessages = [
            ...messages,
            { role: 'user', content: userMessage },
        ];
        setMessages(updatedMessages);
        setLoading(true);
        try {
            const chatRequest = {
                message: userMessage,
                conversation_history: updatedMessages,
                user_preferences: requestPreferences,
            };
            const response = await api.chat(chatRequest);
            const mergedPreferences = response.updated_preferences
                ? {
                    ...requestPreferences,
                    ...response.updated_preferences,
                    custom_notes: response.updated_preferences.custom_notes ?? requestPreferences.custom_notes,
                }
                : requestPreferences;
            onPreferencesUpdate(mergedPreferences);
            // Add assistant response
            setMessages((prev) => [
                ...prev,
                { role: 'assistant', content: response.reply },
            ]);
            // Store suggested searches
            setSuggestedSearches(response.suggested_searches);
            if (response.should_search) {
                await onSearch(mergedPreferences);
            }
        }
        catch (error) {
            console.error('Chat error:', error);
            setMessages((prev) => [
                ...prev,
                {
                    role: 'assistant',
                    content: "Sorry, I encountered an error. Please try again or use the preference builder on the right.",
                },
            ]);
        }
        finally {
            setLoading(false);
        }
    };
    const handleSuggestedSearch = async (suggestion) => {
        if (suggestion.includes('Search restaurants')) {
            await onSearch();
        }
    };
    return (_jsxs("div", { className: "chat-interface", children: [_jsxs("div", { className: "chat-messages", children: [messages.map((msg, idx) => (_jsxs("div", { className: `message message-${msg.role}`, children: [_jsx("div", { className: "message-avatar", children: msg.role === 'user' ? '👤' : '🤖' }), _jsx("div", { className: "message-content", children: _jsx("p", { children: msg.content }) })] }, idx))), loading && (_jsxs("div", { className: "message message-assistant", children: [_jsx("div", { className: "message-avatar", children: "\uD83E\uDD16" }), _jsx("div", { className: "message-content", children: _jsxs("div", { className: "loading-dots", children: [_jsx("span", {}), _jsx("span", {}), _jsx("span", {})] }) })] })), _jsx("div", { ref: messagesEndRef })] }), suggestedSearches.length > 0 && (_jsxs("div", { className: "suggested-searches", children: [_jsx("label", { children: "\uD83D\uDCA1 Suggested:" }), _jsx("div", { className: "search-buttons", children: suggestedSearches.map((suggestion, idx) => (_jsx("button", { className: "suggestion-btn", onClick: () => handleSuggestedSearch(suggestion), children: suggestion }, idx))) })] })), _jsxs("form", { onSubmit: handleSendMessage, className: "chat-input-form", children: [_jsx("input", { type: "text", placeholder: "Tell me about your dietary preferences...", value: input, onChange: (e) => setInput(e.target.value), disabled: loading, className: "chat-input" }), _jsx("button", { type: "submit", disabled: loading, className: "send-btn", children: loading ? _jsx(Loader, { size: 20 }) : _jsx(Send, { size: 20 }) })] })] }));
}
