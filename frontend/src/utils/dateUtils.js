/**
 * Date formatting utilities
 */

/**
 * Formats a date string to a readable format
 * Handles various backend date formats: ISO 8601, DD-MM-YYYY, DD/MM/YYYY, etc.
 * @param {string} dateStr - The date string to format
 * @param {Object} options - Formatting options
 * @returns {string} Formatted date string
 */
export const formatDate = (dateStr, options = {}) => {
    if (!dateStr) return 'N/A';

    try {
        // Try parsing the date
        let date;

        // Handle DD-MM-YYYY or DD/MM/YYYY format
        if (/^\d{1,2}[-/]\d{1,2}[-/]\d{4}$/.test(dateStr)) {
            const parts = dateStr.split(/[-/]/);
            // Assuming DD-MM-YYYY format from Indian APIs
            date = new Date(parts[2], parts[1] - 1, parts[0]);
        } else {
            // Try ISO format or other formats JavaScript Date can parse
            date = new Date(dateStr);
        }

        // Check if date is valid
        if (isNaN(date.getTime())) {
            return dateStr; // Return original if parsing failed
        }

        // Default format: locale date string
        const defaultOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            ...options,
        };

        return date.toLocaleDateString('en-IN', defaultOptions);
    } catch (error) {
        console.error('Error formatting date:', error);
        return dateStr; // Return original on error
    }
};

/**
 * Formats a date to relative time (e.g., "2 days ago")
 * @param {string|Date} date - The date to format
 * @returns {string} Relative time string
 */
export const formatRelativeTime = (date) => {
    if (!date) return 'N/A';

    try {
        const dateObj = typeof date === 'string' ? new Date(date) : date;
        const now = new Date();
        const diffInSeconds = Math.floor((now - dateObj) / 1000);

        if (diffInSeconds < 60) return 'Just now';
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
        if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)} days ago`;

        // For older dates, return formatted date
        return formatDate(dateObj);
    } catch (error) {
        console.error('Error formatting relative time:', error);
        return 'N/A';
    }
};

/**
 * Formats a date to ISO format (YYYY-MM-DD)
 * @param {Date} date - The date to format
 * @returns {string} ISO formatted date string
 */
export const formatToISO = (date) => {
    if (!date) return '';

    try {
        const d = typeof date === 'string' ? new Date(date) : date;
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    } catch (error) {
        console.error('Error formatting to ISO:', error);
        return '';
    }
};
