import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { X, Search } from 'lucide-react';
import './PreferenceBuilder.css';
export default function PreferenceBuilder({ preferences, onPreferencesChange, onSearch, loading, }) {
    const removeAllergen = (allergen) => {
        const updated = {
            ...preferences,
            allergens: preferences.allergens.filter((a) => a !== allergen),
        };
        onPreferencesChange(updated);
    };
    const removeDietaryStyle = (style) => {
        const updated = {
            ...preferences,
            dietary_styles: preferences.dietary_styles.filter((s) => s !== style),
        };
        onPreferencesChange(updated);
    };
    const removeCuisine = (cuisine) => {
        const updated = {
            ...preferences,
            preferred_cuisines: preferences.preferred_cuisines.filter((c) => c !== cuisine),
        };
        onPreferencesChange(updated);
    };
    const hasPreferences = preferences.allergens.length > 0 ||
        preferences.dietary_styles.length > 0 ||
        preferences.preferred_cuisines.length > 0;
    return (_jsxs("div", { className: "preference-builder", children: [_jsx("h3", { children: "Your Preferences" }), !hasPreferences && (_jsx("p", { className: "no-prefs-message", children: "Talk to the chatbot to build your preferences..." })), preferences.allergens.length > 0 && (_jsxs("div", { className: "pref-section", children: [_jsx("label", { className: "pref-label", children: "\uD83D\uDEAB Allergens" }), _jsx("div", { className: "pref-tags", children: preferences.allergens.map((allergen) => (_jsxs("span", { className: "pref-tag allergen-tag", children: [_jsx("span", { children: allergen }), _jsx("button", { onClick: () => removeAllergen(allergen), className: "tag-remove", title: `Remove ${allergen}`, children: _jsx(X, { size: 14 }) })] }, allergen))) })] })), preferences.dietary_styles.length > 0 && (_jsxs("div", { className: "pref-section", children: [_jsx("label", { className: "pref-label", children: "\uD83E\uDD57 Diet" }), _jsx("div", { className: "pref-tags", children: preferences.dietary_styles.map((style) => (_jsxs("span", { className: "pref-tag diet-tag", children: [_jsx("span", { children: style }), _jsx("button", { onClick: () => removeDietaryStyle(style), className: "tag-remove", title: `Remove ${style}`, children: _jsx(X, { size: 14 }) })] }, style))) })] })), preferences.preferred_cuisines.length > 0 && (_jsxs("div", { className: "pref-section", children: [_jsx("label", { className: "pref-label", children: "\uD83C\uDF5C Cuisines" }), _jsx("div", { className: "pref-tags", children: preferences.preferred_cuisines.map((cuisine) => (_jsxs("span", { className: "pref-tag cuisine-tag", children: [_jsx("span", { children: cuisine }), _jsx("button", { onClick: () => removeCuisine(cuisine), className: "tag-remove", title: `Remove ${cuisine}`, children: _jsx(X, { size: 14 }) })] }, cuisine))) })] })), hasPreferences && (_jsxs("button", { className: "search-btn", onClick: onSearch, disabled: loading, children: [_jsx(Search, { size: 16 }), loading ? 'Searching...' : 'Search Restaurants'] }))] }));
}
