/**
 * ResumeAI Desktop - Main Application
 */

class ResumeAIDesktop {
    constructor() {
        this.currentView = 'dashboard';
        this.api = null;
        this.storage = null;
        this.toast = null;
        this.modal = null;
        this.charts = null;
        this.utils = null;
        
        // View controllers
        this.dashboard = null;
        this.resume = null;
        this.generate = null;
        this.tracking = null;
        this.analytics = null;
        this.settings = null;
    }

    /**
     * Initialize the application
     */
    async init() {
        try {
            // Initialize core services
            this.utils = window.Utils;
            this.storage = new StorageManager();
            await this.storage.init();
            
            this.api = new APIClient('http://localhost:8000');
            
            // Set API key from storage
            const settings = this.storage.settings;
            const apiKey = settings.apiProvider === 'anthropic' 
                ? settings.anthropicKey 
                : settings.openaiKey;
            if (apiKey) {
                this.api.setApiKey(apiKey);
            }

            // Initialize components
            this.toast = new ToastManager();
            this.modal = new ModalManager();
            this.charts = new ChartsManager();

            // Initialize view controllers
            this.dashboard = new DashboardView(this);
            this.resume = new ResumeView(this);
            this.generate = new GenerateView(this);
            this.tracking = new TrackingView(this);
            this.analytics = new AnalyticsView(this);
            this.settings = new SettingsView(this);

            // Setup navigation
            this.setupNavigation();

            // Setup connection monitoring
            this.setupConnectionMonitoring();

            // Request notification permission if enabled
            if (settings.enableNotifications) {
                this.utils.requestNotificationPermission();
            }

            console.log('ResumeAI Desktop initialized');
            
        } catch (error) {
            console.error('Initialization error:', error);
            this.toast.error('Failed to initialize application');
        }
    }

    /**
     * Setup navigation
     */
    setupNavigation() {
        document.querySelectorAll('.nav-item').forEach((item) => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const view = item.dataset.view;
                this.navigate(view);
            });
        });
    }

    /**
     * Navigate to a view
     */
    navigate(viewName) {
        // Update nav items
        document.querySelectorAll('.nav-item').forEach((item) => {
            item.classList.toggle('active', item.dataset.view === viewName);
        });

        // Update views
        document.querySelectorAll('.view').forEach((view) => {
            view.classList.toggle('active', view.id === `view-${viewName}`);
        });

        this.currentView = viewName;

        // Trigger view-specific load
        if (this[viewName] && this[viewName].load) {
            this[viewName].load();
        }

        // Special handling for analytics (lazy load charts)
        if (viewName === 'analytics' && this.analytics) {
            setTimeout(() => this.analytics.loadAnalytics(), 100);
        }
    }

    /**
     * Setup connection monitoring
     */
    setupConnectionMonitoring() {
        const updateConnectionStatus = () => {
            const statusDot = document.querySelector('.status-dot');
            const statusText = document.querySelector('.status-text');
            
            if (this.utils.isOnline()) {
                statusDot?.classList.remove('offline');
                statusDot?.classList.add('online');
                statusText.textContent = 'Online';
            } else {
                statusDot?.classList.remove('online');
                statusDot?.classList.add('offline');
                statusText.textContent = 'Offline Mode';
            }
        };

        window.addEventListener('online', updateConnectionStatus);
        window.addEventListener('offline', updateConnectionStatus);
        
        // Initial check
        updateConnectionStatus();

        // Periodic API health check
        setInterval(async () => {
            if (this.utils.isOnline() && this.api) {
                const healthy = await this.api.healthCheck();
                if (healthy) {
                    const statusDot = document.querySelector('.status-dot');
                    statusDot?.classList.add('online');
                    statusDot?.classList.remove('offline');
                }
            }
        }, 30000); // Check every 30 seconds
    }

    /**
     * Download a file
     */
    downloadFile(path) {
        if (this.generate) {
            this.generate.downloadFile(path);
        }
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        this.toast.show(message, type);
    }

    /**
     * Show modal dialog
     */
    showModal(options) {
        this.modal.open(options);
    }

    /**
     * Refresh current view
     */
    refresh() {
        if (this[this.currentView] && this[this.currentView].refresh) {
            this[this.currentView].refresh();
        }
    }
}

// Initialize app when DOM is ready
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new ResumeAIDesktop();
    app.init();
    
    // Expose app globally for debugging and inline handlers
    window.app = app;
});

// Export for use in other modules
window.ResumeAIDesktop = ResumeAIDesktop;
