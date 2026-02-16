/**
 * ResumeAI Desktop - Tracking View Controller
 */

class TrackingView {
    constructor(app) {
        this.app = app;
        this.storage = app.storage;
        this.api = app.api;
        this.toast = app.toast;
        this.utils = app.utils;
        
        this.applications = [];
        this.filteredApplications = [];
        
        this.init();
    }

    /**
     * Initialize tracking view
     */
    init() {
        this.bindEvents();
        this.loadApplications();
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // Toggle add form
        document.getElementById('toggleAddForm')?.addEventListener('click', () => {
            this.toggleAddForm();
        });

        document.getElementById('cancelAddForm')?.addEventListener('click', () => {
            this.hideAddForm();
        });

        // Add application form
        document.getElementById('addApplicationForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.addApplication();
        });

        // Search and filter
        document.getElementById('searchApplications')?.addEventListener('input', (e) => {
            this.filterApplications();
        });

        document.getElementById('filterStatus')?.addEventListener('change', () => {
            this.filterApplications();
        });

        // Export button
        document.getElementById('exportTracking')?.addEventListener('click', () => {
            this.exportToCSV();
        });
    }

    /**
     * Toggle add form visibility
     */
    toggleAddForm() {
        const form = document.getElementById('addApplicationForm');
        if (form.classList.contains('hidden')) {
            this.showAddForm();
        } else {
            this.hideAddForm();
        }
    }

    /**
     * Show add form
     */
    showAddForm() {
        document.getElementById('addApplicationForm').classList.remove('hidden');
        document.getElementById('appCompany').focus();
    }

    /**
     * Hide add form
     */
    hideAddForm() {
        document.getElementById('addApplicationForm').classList.add('hidden');
        document.getElementById('addApplicationForm').reset();
    }

    /**
     * Load applications from storage
     */
    async loadApplications() {
        try {
            this.applications = await this.storage.getAllApplications();
            this.filteredApplications = [...this.applications];
            this.renderApplications();
        } catch (error) {
            console.error('Load applications error:', error);
            this.toast.error('Failed to load applications');
        }
    }

    /**
     * Add new application
     */
    async addApplication() {
        const company = document.getElementById('appCompany').value.trim();
        const role = document.getElementById('appRole').value.trim();
        const status = document.getElementById('appStatus').value;
        const variant = document.getElementById('appVariant').value;
        const source = document.getElementById('appSource').value;
        const url = document.getElementById('appUrl').value.trim();
        const notes = document.getElementById('appNotes').value.trim();

        if (!company) {
            this.toast.error('Company name is required');
            return;
        }

        try {
            const application = {
                company,
                role: role || 'Software Engineer',
                status,
                variant,
                source,
                url: url || null,
                notes: notes || null,
            };

            const id = await this.storage.addApplication(application);
            application.id = id;
            application.date = new Date().toISOString();
            
            this.applications.unshift(application);
            this.filteredApplications = [...this.applications];
            
            this.renderApplications();
            this.hideAddForm();
            this.toast.success(`Application added: ${company}`);
            
            // Refresh dashboard
            if (this.app.dashboard) {
                this.app.dashboard.refresh();
            }
            
        } catch (error) {
            console.error('Add application error:', error);
            this.toast.error('Failed to add application');
        }
    }

    /**
     * Filter applications based on search and status
     */
    filterApplications() {
        const searchQuery = document.getElementById('searchApplications').value.toLowerCase();
        const statusFilter = document.getElementById('filterStatus').value;

        this.filteredApplications = this.applications.filter((app) => {
            const matchesSearch = !searchQuery ||
                app.company.toLowerCase().includes(searchQuery) ||
                (app.role && app.role.toLowerCase().includes(searchQuery)) ||
                (app.notes && app.notes.toLowerCase().includes(searchQuery));

            const matchesStatus = !statusFilter || app.status === statusFilter;

            return matchesSearch && matchesStatus;
        });

        this.renderApplications();
    }

    /**
     * Render applications table
     */
    renderApplications() {
        const tbody = document.getElementById('applicationsBody');

        if (this.filteredApplications.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-muted">
                        ${this.applications.length === 0 
                            ? 'No applications yet. Add your first application!' 
                            : 'No applications match your filters.'}
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = this.filteredApplications
            .map(
                (app) => `
                <tr data-id="${app.id}">
                    <td>
                        <strong>${this.utils.escapeHTML(app.company)}</strong>
                        ${app.url ? `<br><a href="${this.utils.escapeHTML(app.url)}" target="_blank" class="text-muted" style="font-size: 0.75rem;">View Job</a>` : ''}
                    </td>
                    <td>${this.utils.escapeHTML(app.role || 'N/A')}</td>
                    <td><span class="${this.utils.getStatusClass(app.status)}">${app.status}</span></td>
                    <td>${this.utils.escapeHTML(app.variant || 'N/A')}</td>
                    <td>${this.utils.escapeHTML(app.source || 'N/A')}</td>
                    <td>${this.utils.formatDate(app.date)}</td>
                    <td>
                        <div class="btn-group">
                            <button class="btn btn-sm" onclick="app.tracking.updateStatus(${app.id})" title="Update Status">
                                📝
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="app.tracking.deleteApplication(${app.id})" title="Delete">
                                🗑️
                            </button>
                        </div>
                    </td>
                </tr>
            `
            )
            .join('');
    }

    /**
     * Update application status
     */
    async updateStatus(id) {
        const app = this.applications.find((a) => a.id === id);
        if (!app) return;

        const statuses = ['applied', 'screening', 'interview', 'offer', 'rejected', 'withdrawn'];
        const currentIndex = statuses.indexOf(app.status);
        
        // Create a simple modal to select new status
        const newStatus = await this.app.modal.prompt({
            title: 'Update Status',
            message: `Current status: ${app.status}`,
            defaultValue: app.status,
            placeholder: 'Enter new status',
        });

        if (newStatus && statuses.includes(newStatus.toLowerCase())) {
            try {
                await this.storage.updateApplicationStatus(id, newStatus.toLowerCase());
                app.status = newStatus.toLowerCase();
                app.updatedAt = new Date().toISOString();
                this.renderApplications();
                this.toast.success(`Status updated to ${newStatus}`);
                
                // Refresh dashboard
                if (this.app.dashboard) {
                    this.app.dashboard.refresh();
                }
            } catch (error) {
                console.error('Update status error:', error);
                this.toast.error('Failed to update status');
            }
        }
    }

    /**
     * Delete application
     */
    async deleteApplication(id) {
        const confirmed = await this.app.modal.confirm({
            title: 'Delete Application',
            message: 'Are you sure you want to delete this application?',
            confirmText: 'Delete',
            type: 'danger',
        });

        if (!confirmed) return;

        try {
            await this.storage.deleteApplication(id);
            this.applications = this.applications.filter((a) => a.id !== id);
            this.filteredApplications = this.filteredApplications.filter((a) => a.id !== id);
            this.renderApplications();
            this.toast.success('Application deleted');
            
            // Refresh dashboard
            if (this.app.dashboard) {
                this.app.dashboard.refresh();
            }
        } catch (error) {
            console.error('Delete application error:', error);
            this.toast.error('Failed to delete application');
        }
    }

    /**
     * Export applications to CSV
     */
    async exportToCSV() {
        try {
            const applications = await this.storage.getAllApplications();
            
            if (applications.length === 0) {
                this.toast.warning('No applications to export');
                return;
            }

            // Create CSV content
            const headers = ['ID', 'Company', 'Role', 'Status', 'Variant', 'Source', 'URL', 'Notes', 'Date', 'Updated'];
            const rows = applications.map((app) => [
                app.id,
                `"${(app.company || '').replace(/"/g, '""')}"`,
                `"${(app.role || '').replace(/"/g, '""')}"`,
                app.status,
                app.variant || '',
                app.source || '',
                `"${(app.url || '').replace(/"/g, '""')}"`,
                `"${(app.notes || '').replace(/"/g, '""')}"`,
                app.date,
                app.updatedAt || '',
            ]);

            const csv = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n');
            
            // Download CSV
            const filename = `applications-${new Date().toISOString().split('T')[0]}.csv`;
            this.utils.downloadFile(csv, filename, 'text/csv');
            
            this.toast.success(`Exported ${applications.length} applications`);
        } catch (error) {
            console.error('Export error:', error);
            this.toast.error('Failed to export applications');
        }
    }

    /**
     * Refresh applications
     */
    refresh() {
        this.loadApplications();
    }
}

// Export for use in other modules
window.TrackingView = TrackingView;
