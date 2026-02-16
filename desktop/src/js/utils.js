/**
 * ResumeAI Desktop - Utility Functions
 */

const Utils = {
    /**
     * Format date to readable string
     */
    formatDate(dateString, options = {}) {
        const date = new Date(dateString);
        const defaultOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
        };
        return date.toLocaleDateString('en-US', { ...defaultOptions, ...options });
    },

    /**
     * Format date to relative time (e.g., "2 hours ago")
     */
    formatRelative(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        
        return this.formatDate(dateString);
    },

    /**
     * Truncate text to specified length
     */
    truncate(text, maxLength = 50, suffix = '...') {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength - suffix.length) + suffix;
    },

    /**
     * Escape HTML special characters
     */
    escapeHTML(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * Generate unique ID
     */
    generateId() {
        return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    },

    /**
     * Debounce function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Throttle function
     */
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => (inThrottle = false), limit);
            }
        };
    },

    /**
     * Parse YAML-like text (simple parser for basic structures)
     */
    parseSimpleYAML(text) {
        try {
            // This is a very basic YAML parser for display purposes
            // For production, use a proper YAML library
            const lines = text.split('\n');
            const result = {};
            let currentKey = null;
            let currentIndent = 0;

            for (const line of lines) {
                if (!line.trim() || line.trim().startsWith('#')) continue;

                const indent = line.search(/\S/);
                const content = line.trim();

                if (indent === 0) {
                    if (content.includes(':')) {
                        const [key, value] = content.split(':').map((s) => s.trim());
                        currentKey = key;
                        result[key] = value || {};
                        currentIndent = 0;
                    }
                } else if (currentKey && content.includes(':')) {
                    const [key, value] = content.split(':').map((s) => s.trim());
                    if (typeof result[currentKey] === 'object') {
                        result[currentKey][key] = value || '';
                    }
                }
            }

            return result;
        } catch (error) {
            console.error('YAML parse error:', error);
            return null;
        }
    },

    /**
     * Convert Markdown to HTML (basic conversion)
     */
    markdownToHTML(markdown) {
        if (!markdown) return '';

        let html = markdown
            // Headers
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            // Bold
            .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
            // Italic
            .replace(/\*(.*)\*/gim, '<em>$1</em>')
            // Links
            .replace(/\[([^\]]+)\]\(([^)]+)\)/gim, '<a href="$2" target="_blank">$1</a>')
            // Line breaks
            .replace(/\n/gim, '<br>');

        return html;
    },

    /**
     * Download file
     */
    downloadFile(content, filename, mimeType = 'text/plain') {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    },

    /**
     * Read file as text
     */
    readFileAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(e);
            reader.readAsText(file);
        });
    },

    /**
     * Copy text to clipboard
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (error) {
            // Fallback for older browsers
            const textarea = document.createElement('textarea');
            textarea.value = text;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            return true;
        }
    },

    /**
     * Check if online
     */
    isOnline() {
        return navigator.onLine;
    },

    /**
     * Get status badge class
     */
    getStatusClass(status) {
        const classes = {
            applied: 'status-badge applied',
            screening: 'status-badge screening',
            interview: 'status-badge interview',
            offer: 'status-badge offer',
            rejected: 'status-badge rejected',
            withdrawn: 'status-badge withdrawn',
        };
        return classes[status] || 'status-badge';
    },

    /**
     * Format number with commas
     */
    formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },

    /**
     * Calculate percentage
     */
    calculatePercentage(part, total, decimals = 0) {
        if (!total) return 0;
        return ((part / total) * 100).toFixed(decimals);
    },

    /**
     * Group array by key
     */
    groupBy(array, key) {
        return array.reduce((result, item) => {
            const group = item[key];
            if (!result[group]) {
                result[group] = [];
            }
            result[group].push(item);
            return result;
        }, {});
    },

    /**
     * Sort array by key
     */
    sortBy(array, key, ascending = true) {
        return [...array].sort((a, b) => {
            const aVal = a[key];
            const bVal = b[key];
            if (aVal < bVal) return ascending ? -1 : 1;
            if (aVal > bVal) return ascending ? 1 : -1;
            return 0;
        });
    },

    /**
     * Show notification (using Web Notifications API)
     */
    showNotification(title, options = {}) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, {
                icon: '/icons/icon-192.png',
                ...options,
            });
        }
    },

    /**
     * Request notification permission
     */
    async requestNotificationPermission() {
        if ('Notification' in window) {
            const permission = await Notification.requestPermission();
            return permission === 'granted';
        }
        return false;
    },

    /**
     * Extract company name from job description
     */
    extractCompanyName(text) {
        // Simple heuristic - look for common patterns
        const patterns = [
            /(?:at|for|with)\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)/i,
            /([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)\s+(?:is|was|are|were)\s+hiring/i,
            /Company:\s*([A-Z][A-Za-z]+(?:\s+[A-Za-z]+)*)/i,
        ];

        for (const pattern of patterns) {
            const match = text.match(pattern);
            if (match) {
                return match[1].trim();
            }
        }

        return 'Company';
    },

    /**
     * Extract job title from job description
     */
    extractJobTitle(text) {
        const patterns = [
            /(?:hiring|looking for)\s+(?:a|an)?\s*([A-Za-z\s]+)(?:\s*(?:engineer|developer|manager|director|lead))/i,
            /Position:\s*([A-Za-z\s]+)/i,
            /Title:\s*([A-Za-z\s]+)/i,
        ];

        for (const pattern of patterns) {
            const match = text.match(pattern);
            if (match) {
                return match[1].trim();
            }
        }

        return 'Position';
    },
};

// Export for use in other modules
window.Utils = Utils;
