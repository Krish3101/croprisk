// Application constants

// Indian States - Major agricultural states
export const INDIAN_STATES = [
    'Maharashtra',
    'Punjab',
    'Karnataka',
    'Haryana',
    'Rajasthan',
    'Uttar Pradesh',
    'Madhya Pradesh',
    'Gujarat',
    'West Bengal',
    'Tamil Nadu',
    'Andhra Pradesh',
    'Bihar',
];

// Crop Growth Stages
export const CROP_STAGES = [
    'Sown',
    'Germination',
    'Vegetative',
    'Flowering',
    'Fruiting',
    'Harvest Ready',
    'Harvested',
];

// Common crop types for reference
export const COMMON_CROPS = [
    'Wheat',
    'Rice',
    'Cotton',
    'Sugarcane',
    'Tomato',
    'Potato',
    'Onion',
    'Corn',
    'Bajra',
    'Jowar',
];

// Default values (can be overridden by environment variables)
export const DEFAULTS = {
    CITY: import.meta.env.VITE_DEFAULT_CITY || 'Pune',
    STATE: import.meta.env.VITE_DEFAULT_STATE || 'Maharashtra',
    CROP: import.meta.env.VITE_DEFAULT_CROP || 'Wheat',
};
