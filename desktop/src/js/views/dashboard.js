/**
 * ResumeAI Desktop - Dashboard View Controller
 */

class DashboardView {
    constructor(app) {
        this.app = app;
        this.storage = app.storage;
        this.api = app.api;
        this.toast = app.toast;
        this.utils = app.utils;
        
        this.init();
    }

    /**
     * Initialize dashboard
     */
    init() {
        this.bindEvents();
        this.loadDashboard();
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // Refresh button
        document.getElementById('refreshDashboard')?.addEventListener('click', () => {
            this.loadDashboard();
        });

        // Quick action buttons
        document.querySelectorAll('[data-action]').forEach((btn) => {
            btn.addEventListener('click', (e) => {
                const action = e.currentTarget.dataset.action;
                this.handleQuickAction(action);
            });
        });
    }

    /**
     * Handle quick action buttons
     */
    handleQuickAction(action) {
        switch (action) {
            case 'new-application':
                this.app.navigate('tracking');
                document.getElementById('toggleAddForm')?.click();
                break;
            case 'generate-resume':
                this.app.navigate('generate');
                break;
            case 'upload-job-desc':
                this.app.navigate('generate');
                document.getElementById('jobDescFile')?.click();
                break;
            case 'view-analytics':
                this.app.navigate('analytics');
                break;
        }
    }

    /**
     * Load dashboard data
     */
    async loadDashboard() {
        try {
            await this.loadOverview();
            await this.loadRecentActivity();
        } catch (error) {
            console.error('Dashboard load error:', error);
            this.toast.error('Failed to load dashboard data');
        }
    }

    /**
     * Load overview statistics
     */
    async loadOverview() {
        try {
            // Try to get data from API first
            let overview;
            if (this.api && await this.api.healthCheck()) {
                overview = await this.api.getAnalyticsOverview();
            }
            
            // Fall back to local storage
            if (!overview) {
                const applications = await this.storage.getAllApplications();
                overview = this.calculateOverview(applications);
            }

            // Update UI
            this.updateOverviewUI(overview);
        } catch (error) {
            console.error('Overview load error:', error);
            // Use local data as fallback
            const applications = await this.storage.getAllApplications();
            const overview = this.calculateOverview(applications);
            this.updateOverviewUI(overview);
        }
    }

    /**
     * Calculate overview from local data
     */
    calculateOverview(applications) {
        const total = applications.length;
        const interviews = applications.filter((app) => app.status === 'interview').length;
        const offers = applications.filter((app) => app.status === 'offer').length;
        const responseRate = total > 0 
            ? (((applications.filter((app) => ['interview', 'offer'].includes(app.status)).length) / total) * 100).toFixed(1)
            : 0;

        return {
            total_applications: total,
            interviews,
            offers,
            response_rate: parseFloat(responseRate),
        };
    }

    /**
     * Update overview UI
     */
    updateOverviewUI(overview) {
        // Update stat cards
        document.getElementById('stat-total').textContent = overview.total_applications || 0;
        document.getElementById('stat-interviews').textContent = overview.interviews || 0;
        document.getElementById('stat-offers').textContent = overview.offers || 0;
        document.getElementById('stat-response-rate').textContent = `${overview.response_rate || 0}%`;
    }

    /**
     * Load recent activity
     */
    async loadRecentActivity() {
        try {
            const applications = await this.storage.getAllApplications();
            const recent = applications.slice(0, 5);
            this.renderRecentActivity(recent);
        } catch (error) {
            console.error('Recent activity load error:', error);
            document.getElementById('recentActivity').innerHTML = `
                <p class="text-muted">Unable to load recent activity</p>
            `;
        }
    }

    /**
     * Render recent activity list
     */
    renderRecentActivity(applications) {
        const container = document.getElementById('recentActivity');
        
        if (applications.length === 0) {
            container.innerHTML = `
                <p class="text-muted">No recent activity. Start by adding applications!</p>
            `;
            return;
        }

        const icons = {
            applied: '📤',
            screening: '🔍',
            interview: '💬',
            offer: '🎉',
            rejected: '❌',
            withdrawn: '🚫',
        };

        container.innerHTML = applications
            .map(
                (app) => `
                <div class="activity-item">
                    <span class="activity-icon">${icons[app.status] || '📋'}</span>
                    <div class="activity-content">
                        <div class="activity-title">
                            ${this.utils.escapeHTML(app.company)}
                            ${app.role ? ` - ${this.utils.escapeHTML(app.role)}` : ''}
                        </div>
                        <div class="activity-time">${this.utils.formatRelative(app.date)}</div>
                    </div>
                    <span class="status-badge ${app.status}">${app.status}</span>
                </div>
            `
            )
            .join('');
    }

    /**
     * Refresh dashboard
     */
    refresh() {
        this.loadDashboard();
    }
}

// Export for use in other modules
window.DashboardView = DashboardView;
