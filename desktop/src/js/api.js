/**
 * ResumeAI Desktop - API Client
 * Handles communication with the Resume CLI API backend
 */

class APIClient {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
        this.apiKey = null;
        this.timeout = 30000; // 30 seconds
    }

    /**
     * Set API key for authentication
     */
    setApiKey(key) {
        this.apiKey = key;
    }

    /**
     * Build URL from endpoint
     */
    buildURL(endpoint) {
        return `${this.baseURL}${endpoint}`;
    }

    /**
     * Get headers for API requests
     */
    getHeaders(contentType = 'application/json') {
        const headers = {
            'Content-Type': contentType,
        };
        
        if (this.apiKey) {
            headers['X-API-Key'] = this.apiKey;
        }
        
        return headers;
    }

    /**
     * Generic request handler
     */
    async request(endpoint, options = {}) {
        const url = this.buildURL(endpoint);
        const config = {
            ...options,
            headers: {
                ...this.getHeaders(options.contentType),
                ...options.headers,
            },
        };

        // Add timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);
        config.signal = controller.signal;

        try {
            const response = await fetch(url, config);
            clearTimeout(timeoutId);

            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: response.statusText }));
                throw new APIError(error.detail || `HTTP ${response.status}`, response.status);
            }

            // Handle different response types
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            if (contentType && contentType.includes('text/')) {
                return await response.text();
            }

            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new APIError('Request timeout', 408);
            }
            if (error instanceof APIError) {
                throw error;
            }
            throw new APIError(`Network error: ${error.message}`, 0);
        }
    }

    /**
     * Health check endpoint
     */
    async healthCheck() {
        try {
            const response = await this.request('/health');
            return response.status === 'healthy';
        } catch (error) {
            return false;
        }
    }

    /**
     * Get available resume variants
     */
    async getVariants() {
        return this.request('/v1/variants');
    }

    /**
     * Render resume as PDF
     */
    async renderPDF(resumeData, variant = 'v1.0.0-base') {
        return this.request('/v1/render/pdf', {
            method: 'POST',
            body: JSON.stringify({
                resume_data: resumeData,
                variant: variant,
            }),
        });
    }

    /**
     * AI-tailor resume for job description
     */
    async tailorResume(resumeData, jobDescription) {
        return this.request('/v1/tailor', {
            method: 'POST',
            body: JSON.stringify({
                resume_data: resumeData,
                job_description: jobDescription,
            }),
        });
    }

    /**
     * Check ATS compatibility score
     */
    async checkATS(resumeData, jobDescription, variant = 'v1.0.0-base') {
        return this.request('/v1/ats/check', {
            method: 'POST',
            body: JSON.stringify({
                resume_data: resumeData,
                job_description: jobDescription,
                variant: variant,
            }),
        });
    }

    /**
     * Generate cover letter
     */
    async generateCoverLetter(resumeData, jobDescription, companyName, variant = 'v1.0.0-base', format = 'md') {
        return this.request('/v1/cover-letter', {
            method: 'POST',
            body: JSON.stringify({
                resume_data: resumeData,
                job_description: jobDescription,
                company_name: companyName,
                variant: variant,
                format: format,
            }),
        });
    }

    /**
     * Analytics - Get overview metrics
     */
    async getAnalyticsOverview() {
        return this.request('/v1/analytics/overview');
    }

    /**
     * Analytics - Get applications by status
     */
    async getAnalyticsByStatus() {
        return this.request('/v1/analytics/by-status');
    }

    /**
     * Analytics - Get timeline data
     */
    async getAnalyticsTimeline(days = 90) {
        return this.request(`/v1/analytics/timeline?days=${days}`);
    }

    /**
     * Analytics - Get variant performance
     */
    async getAnalyticsVariants() {
        return this.request('/v1/analytics/variants');
    }

    /**
     * Analytics - Get company analytics
     */
    async getAnalyticsCompanies() {
        return this.request('/v1/analytics/companies');
    }

    /**
     * Analytics - Get source breakdown
     */
    async getAnalyticsSources() {
        return this.request('/v1/analytics/sources');
    }

    /**
     * Analytics - Get complete dashboard data
     */
    async getDashboardData() {
        return this.request('/v1/analytics/dashboard');
    }

    /**
     * Test API connection
     */
    async testConnection() {
        try {
            const healthy = await this.healthCheck();
            return {
                connected: healthy,
                url: this.baseURL,
            };
        } catch (error) {
            return {
                connected: false,
                error: error.message,
            };
        }
    }
}

/**
 * API Error class
 */
class APIError extends Error {
    constructor(message, status) {
        super(message);
        this.name = 'APIError';
        this.status = status;
    }
}

// Export for use in other modules
window.APIClient = APIClient;
window.APIError = APIError;
