import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { Star, MapPin, Phone, Globe, AlertTriangle, Check } from 'lucide-react';
import './RestaurantResults.css';
export default function RestaurantResults({ restaurants, preferences, loading, }) {
    if (loading) {
        return (_jsx("div", { className: "restaurant-results", children: _jsxs("div", { className: "loading-message", children: [_jsx("div", { className: "spinner" }), _jsx("p", { children: "Finding perfect restaurants for you..." })] }) }));
    }
    if (restaurants.length === 0) {
        return (_jsx("div", { className: "restaurant-results", children: _jsx("div", { className: "empty-message", children: _jsx("p", { children: "No restaurants found. Try adjusting your preferences." }) }) }));
    }
    const getRiskColor = (risk) => {
        switch (risk.toUpperCase()) {
            case 'SAFE':
                return '#10b981';
            case 'LOW_RISK':
                return '#3b82f6';
            case 'MEDIUM_RISK':
                return '#f59e0b';
            case 'HIGH_RISK':
                return '#ef4444';
            default:
                return '#6b7280';
        }
    };
    return (_jsxs("div", { className: "restaurant-results", children: [_jsxs("div", { className: "results-header", children: [_jsxs("h2", { children: ["Found ", restaurants.length, " Restaurants"] }), _jsx("p", { className: "results-summary", children: preferences.location && `Near ${preferences.location}` })] }), _jsx("div", { className: "restaurants-grid", children: restaurants.map((restaurant) => {
                    const cuisines = restaurant.cuisines ?? restaurant.cuisine_types ?? [];
                    const allergenReport = restaurant.allergen_report ?? restaurant.allergen_safety;
                    const recommendedDishes = restaurant.recommended_dishes ?? restaurant.safe_menu_items ?? [];
                    const isOpen = restaurant.is_open ?? restaurant.is_open_now ?? false;
                    return (_jsxs("div", { className: "restaurant-card", children: [_jsxs("div", { className: "card-header", children: [_jsxs("div", { children: [_jsx("h3", { children: restaurant.name }), _jsxs("div", { className: "restaurant-meta", children: [_jsxs("span", { className: "rating", children: [_jsx(Star, { size: 14, fill: "currentColor" }), restaurant.rating.toFixed(1)] }), _jsxs("span", { className: "review-count", children: ["(", restaurant.review_count, " reviews)"] })] })] }), _jsxs("div", { className: "match-score", children: [_jsxs("div", { className: "score-badge", style: {
                                                    background: `hsl(${(restaurant.match_score * 1.2) % 360}, 70%, 50%)`,
                                                }, children: [Math.round(restaurant.match_score), "%"] }), _jsx("span", { className: "score-label", children: "Match" })] })] }), _jsx("div", { className: "cuisines", children: cuisines.map((cuisine) => (_jsx("span", { className: "cuisine-badge", children: cuisine }, cuisine))) }), _jsxs("div", { className: "allergen-section", children: [_jsx("div", { className: `safety-indicator ${allergenReport?.is_safe ? 'safe' : 'warning'}`, children: allergenReport?.is_safe ? (_jsxs(_Fragment, { children: [_jsx(Check, { size: 16 }), _jsx("span", { children: "Allergen Safe" })] })) : (_jsxs(_Fragment, { children: [_jsx(AlertTriangle, { size: 16 }), _jsx("span", { children: "Allergen Warning" })] })) }), _jsxs("div", { className: "safety-score", children: ["Safety Score:", ' ', _jsxs("strong", { style: { color: getRiskColor(allergenReport?.overall_risk ?? 'UNKNOWN') }, children: [allergenReport?.safety_score ?? 0, "/100"] })] })] }), allergenReport?.unsafe_items?.length ? (_jsxs("div", { className: "unsafe-items", children: [_jsx("strong", { className: "warning-label", children: "\u26A0\uFE0F Avoid:" }), _jsxs("div", { className: "items-list", children: [allergenReport.unsafe_items.slice(0, 3).map((item, idx) => (_jsx("span", { className: "unsafe-item", children: item }, idx))), allergenReport.unsafe_items.length > 3 && (_jsxs("span", { className: "more-items", children: ["+", allergenReport.unsafe_items.length - 3, " more"] }))] })] })) : null, recommendedDishes.length > 0 && (_jsxs("div", { className: "recommended-dishes", children: [_jsx("strong", { className: "dishes-label", children: "\u2705 Recommended Dishes:" }), _jsx("div", { className: "dishes-list", children: recommendedDishes.slice(0, 3).map((dish, idx) => (_jsxs("div", { className: "dish-item", children: [_jsx("span", { className: "dish-name", children: dish.name }), dish.price_usd && (_jsxs("span", { className: "dish-price", children: ["$", dish.price_usd.toFixed(2)] }))] }, idx))) })] })), _jsxs("div", { className: "restaurant-details", children: [restaurant.distance_miles !== undefined && (_jsxs("div", { className: "detail-item", children: [_jsx(MapPin, { size: 14 }), _jsxs("span", { children: [restaurant.distance_miles.toFixed(1), " mi away"] })] })), restaurant.phone && (_jsxs("div", { className: "detail-item", children: [_jsx(Phone, { size: 14 }), _jsx("a", { href: `tel:${restaurant.phone}`, children: restaurant.phone })] })), restaurant.url && (_jsxs("div", { className: "detail-item", children: [_jsx(Globe, { size: 14 }), _jsx("a", { href: restaurant.url, target: "_blank", rel: "noopener noreferrer", children: "View on Map" })] }))] }), _jsx("div", { className: "card-status", children: isOpen ? (_jsx("span", { className: "open", children: "\uD83D\uDFE2 Open Now" })) : (_jsx("span", { className: "closed", children: "\uD83D\uDD34 Closed" })) })] }, restaurant.place_id ?? restaurant.yelp_id ?? restaurant.name));
                }) })] }));
}
