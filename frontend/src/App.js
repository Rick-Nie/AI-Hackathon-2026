import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import './App.css';
import ChatInterface from './components/ChatInterface';
import RestaurantResults from './components/RestaurantResults';
import PreferenceBuilder from './components/PreferenceBuilder';
import { SpiceLevel } from './types';
import { api } from './api';
import { MessageCircle, Utensils } from 'lucide-react';
const DEFAULT_PREFERENCES = {
    dietary_styles: [],
    allergens: [],
    disliked_ingredients: [],
    preferred_cuisines: [],
    disliked_cuisines: [],
    max_spice_level: SpiceLevel.MEDIUM,
    max_distance_miles: 5.0,
    min_rating: 3.5,
    requires_open_now: true,
};
function App() {
    const [preferences, setPreferences] = useState(DEFAULT_PREFERENCES);
    const [restaurants, setRestaurants] = useState([]);
    const [loading, setLoading] = useState(false);
    const [tab, setTab] = useState('chat');
    const [hasSearched, setHasSearched] = useState(false);
    const handlePreferencesUpdate = (updatedPrefs) => {
        setPreferences(updatedPrefs);
    };
    const handleSearch = async (overridePrefs) => {
        setLoading(true);
        try {
            const response = await api.searchRestaurants({
                preferences: overridePrefs ?? preferences,
                limit: 10,
            });
            const restaurants = Array.isArray(response.restaurants)
                ? response.restaurants
                : [];
            setRestaurants(restaurants);
            setHasSearched(true);
            setTab('results');
            if (!Array.isArray(response.restaurants)) {
                console.error('Unexpected restaurant search response:', response);
            }
        }
        catch (error) {
            console.error('Search failed:', error);
        }
        finally {
            setLoading(false);
        }
    };
    return (_jsxs("div", { className: "app", children: [_jsx("header", { className: "app-header", children: _jsx("div", { className: "header-content", children: _jsxs("div", { className: "logo", children: [_jsx(Utensils, { size: 32 }), _jsx("h1", { children: "DietMate" }), _jsx("p", { children: "Find restaurants that match YOUR dietary needs" })] }) }) }), _jsxs("div", { className: "container", children: [_jsxs("div", { className: "tab-navigation", children: [_jsxs("button", { className: `tab-btn ${tab === 'chat' ? 'active' : ''}`, onClick: () => setTab('chat'), children: [_jsx(MessageCircle, { size: 20 }), "Chat Assistant"] }), hasSearched && (_jsxs("button", { className: `tab-btn ${tab === 'results' ? 'active' : ''}`, onClick: () => setTab('results'), children: [_jsx(Utensils, { size: 20 }), "Restaurants (", restaurants.length, ")"] }))] }), _jsx("div", { className: "main-content", children: tab === 'chat' ? (_jsxs("div", { className: "chat-section", children: [_jsx(ChatInterface, { preferences: preferences, onPreferencesUpdate: handlePreferencesUpdate, onSearch: handleSearch }), _jsx(PreferenceBuilder, { preferences: preferences, onPreferencesChange: handlePreferencesUpdate, onSearch: handleSearch, loading: loading })] })) : (_jsx(RestaurantResults, { restaurants: restaurants, preferences: preferences, loading: loading })) })] })] }));
}
export default App;
