/**
 * ResumeAI Desktop - Analytics View Controller
 */

class AnalyticsView {
    constructor(app) {
        this.app = app;
        this.storage = app.storage;
        this.api = app.api;
        this.toast = app.toast;
        this.utils = app.utils;
        this.charts = app.charts;
        
        this.init();
    }

    /**
     * Initialize analytics view
     */
    init() {
        this.bindEvents();
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // View visibility listener
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.target.id === 'view-analytics' && 
                    mutation.target.classList.contains('active')) {
                    this.loadAnalytics();
                }
            });
        });

        observer.observe(document.getElementById('view-analytics'), {
            attributes: true,
            attributeFilter: ['class'],
        });
    }

    /**
     * Load analytics data
     */
    async loadAnalytics() {
        try {
            await Promise.all([
                this.loadStatusChart(),
                this.loadTimelineChart(),
                this.loadVariantChart(),
                this.loadSourceChart(),
                this.loadCompanyAnalytics(),
            ]);
        } catch (error) {
            console.error('Analytics load error:', error);
            this.toast.error('Failed to load analytics');
        }
    }

    /**
     * Load status distribution chart
     */
    async loadStatusChart() {
        try {
            let data;
            
            // Try API first
            if (this.api && await this.api.healthCheck()) {
                data = await this.api.getAnalyticsByStatus();
            }
            
            // Fall back to local storage
            if (!data) {
                const applications = await this.storage.getAllApplications();
                data = this.calculateStatusDistribution(applications);
            }

            const labels = Object.keys(data);
            const values = Object.values(data);

            if (labels.length === 0) {
                this.renderEmptyChart('statusChart', 'No data available');
                return;
            }

            this.charts.createPieChart('statusChart', { labels, values }, {
                title: 'Applications by Status',
                type: 'doughnut',
            });
        } catch (error) {
            console.error('Status chart error:', error);
            this.renderEmptyChart('statusChart', 'Failed to load data');
        }
    }

    /**
     * Calculate status distribution from local data
     */
    calculateStatusDistribution(applications) {
        const distribution = {};
        applications.forEach((app) => {
            distribution[app.status] = (distribution[app.status] || 0) + 1;
        });
        return distribution;
    }

    /**
     * Load timeline chart
     */
    async loadTimelineChart() {
        try {
            let data;
            
            // Try API first
            if (this.api && await this.api.healthCheck()) {
                data = await this.api.getAnalyticsTimeline(90);
            }
            
            // Fall back to local storage
            if (!data) {
                const applications = await this.storage.getAllApplications();
                data = this.calculateTimeline(applications, 90);
            }

            const labels = data.map((d) => d.date);
            const values = data.map((d) => d.count);

            if (labels.length === 0) {
                this.renderEmptyChart('timelineChart', 'No data available');
                return;
            }

            this.charts.createLineChart('timelineChart', { labels, values }, {
                title: 'Applications Over Time (90 days)',
                color: '#2563eb',
                fill: true,
            });
        } catch (error) {
            console.error('Timeline chart error:', error);
            this.renderEmptyChart('timelineChart', 'Failed to load data');
        }
    }

    /**
     * Calculate timeline from local data
     */
    calculateTimeline(applications, days) {
        const timeline = {};
        const now = new Date();
        
        // Initialize all dates
        for (let i = days - 1; i >= 0; i--) {
            const date = new Date(now);
            date.setDate(date.getDate() - i);
            const dateStr = date.toISOString().split('T')[0];
            timeline[dateStr] = 0;
        }

        // Count applications per day
        applications.forEach((app) => {
            const dateStr = app.date.split('T')[0];
            if (timeline.hasOwnProperty(dateStr)) {
                timeline[dateStr]++;
            }
        });

        // Convert to array
        return Object.entries(timeline).map(([date, count]) => ({ date, count }));
    }

    /**
     * Load variant performance chart
     */
    async loadVariantChart() {
        try {
            let data;
            
            // Try API first
            if (this.api && await this.api.healthCheck()) {
                data = await this.api.getAnalyticsVariants();
            }
            
            // Fall back to local storage
            if (!data) {
                const applications = await this.storage.getAllApplications();
                data = this.calculateVariantPerformance(applications);
            }

            const labels = data.map((d) => d.variant || 'Unknown');
            const values = data.map((d) => d.total || d.count || 0);

            if (labels.length === 0) {
                this.renderEmptyChart('variantChart', 'No data available');
                return;
            }

            this.charts.createBarChart('variantChart', { labels, values }, {
                title: 'Applications by Resume Variant',
                color: ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#8b5cf6'],
            });
        } catch (error) {
            console.error('Variant chart error:', error);
            this.renderEmptyChart('variantChart', 'Failed to load data');
        }
    }

    /**
     * Calculate variant performance from local data
     */
    calculateVariantPerformance(applications) {
        const performance = {};
        
        applications.forEach((app) => {
            const variant = app.variant || 'Unknown';
            if (!performance[variant]) {
                performance[variant] = {
                    variant,
                    total: 0,
                    interviews: 0,
                    offers: 0,
                };
            }
            performance[variant].total++;
            if (app.status === 'interview') performance[variant].interviews++;
            if (app.status === 'offer') performance[variant].offers++;
        });

        return Object.values(performance);
    }

    /**
     * Load source breakdown chart
     */
    async loadSourceChart() {
        try {
            let data;
            
            // Try API first
            if (this.api && await this.api.healthCheck()) {
                data = await this.api.getAnalyticsSources();
            }
            
            // Fall back to local storage
            if (!data) {
                const applications = await this.storage.getAllApplications();
                data = this.calculateSourceBreakdown(applications);
            }

            const labels = data.map((d) => d.source || 'Unknown');
            const values = data.map((d) => d.count || 0);

            if (labels.length === 0) {
                this.renderEmptyChart('sourceChart', 'No data available');
                return;
            }

            this.charts.createPieChart('sourceChart', { labels, values }, {
                title: 'Applications by Source',
                type: 'pie',
            });
        } catch (error) {
            console.error('Source chart error:', error);
            this.renderEmptyChart('sourceChart', 'Failed to load data');
        }
    }

    /**
     * Calculate source breakdown from local data
     */
    calculateSourceBreakdown(applications) {
        const breakdown = {};
        applications.forEach((app) => {
            const source = app.source || 'Unknown';
            breakdown[source] = (breakdown[source] || 0) + 1;
        });
        return Object.entries(breakdown).map(([source, count]) => ({ source, count }));
    }

    /**
     * Load company analytics
     */
    async loadCompanyAnalytics() {
        try {
            let data;
            
            // Try API first
            if (this.api && await this.api.healthCheck()) {
                data = await this.api.getAnalyticsCompanies();
            }
            
            // Fall back to local storage
            if (!data) {
                const applications = await this.storage.getAllApplications();
                data = this.calculateCompanyAnalytics(applications);
            }

            this.renderCompanyAnalytics(data);
        } catch (error) {
            console.error('Company analytics error:', error);
            document.getElementById('companyAnalytics').innerHTML = `
                <p class="text-muted">Failed to load company analytics</p>
            `;
        }
    }

    /**
     * Calculate company analytics from local data
     */
    calculateCompanyAnalytics(applications) {
        const companies = {};
        
        applications.forEach((app) => {
            const company = app.company || 'Unknown';
            if (!companies[company]) {
                companies[company] = {
                    name: company,
                    applications: 0,
                    statuses: {},
                    roles: new Set(),
                };
            }
            companies[company].applications++;
            companies[company].statuses[app.status] = (companies[company].statuses[app.status] || 0) + 1;
            if (app.role) companies[company].roles.add(app.role);
        });

        return Object.values(companies).sort((a, b) => b.applications - a.applications);
    }

    /**
     * Render company analytics
     */
    renderCompanyAnalytics(companies) {
        const container = document.getElementById('companyAnalytics');

        if (companies.length === 0) {
            container.innerHTML = '<p class="text-muted">Add applications to see company analytics</p>';
            return;
        }

        container.innerHTML = companies
            .slice(0, 10)
            .map(
                (company) => `
                <div class="company-item">
                    <div>
                        <div class="company-name">${this.utils.escapeHTML(company.name)}</div>
                        <div class="text-muted" style="font-size: 0.75rem;">
                            ${Array.from(company.roles).slice(0, 2).join(', ')}
                        </div>
                    </div>
                    <div class="company-stats">
                        <span>${company.applications} applications</span>
                        ${company.statuses.interview ? `<span>💬 ${company.statuses.interview}</span>` : ''}
                        ${company.statuses.offer ? `<span>🎉 ${company.statuses.offer}</span>` : ''}
                    </div>
                </div>
            `
            )
            .join('');
    }

    /**
     * Render empty chart placeholder
     */
    renderEmptyChart(canvasId, message) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        ctx.fillStyle = '#94a3b8';
        ctx.font = '14px -apple-system, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(message, canvas.width / 2, canvas.height / 2);
    }

    /**
     * Refresh analytics
     */
    refresh() {
        this.charts.destroyAll();
        this.loadAnalytics();
    }
}

// Export for use in other modules
window.AnalyticsView = AnalyticsView;
