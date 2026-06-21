import axios from 'axios';
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const apiClient = axios.create({
    baseURL: API_BASE,
    headers: {
        'Content-Type': 'application/json',
    },
});
export const api = {
    health: async () => {
        const response = await apiClient.get('/health');
        return response.data;
    },
    searchRestaurants: async (request) => {
        const response = await apiClient.post('/restaurants/search', request);
        return response.data;
    },
    chat: async (request) => {
        const response = await apiClient.post('/chat', request);
        return response.data;
    },
    checkAllergen: async (dishName, ingredients, userAllergens) => {
        const response = await apiClient.post('/allergen-check', {
            dish_name: dishName,
            ingredients,
            user_allergens: userAllergens,
        });
        return response.data;
    },
};
