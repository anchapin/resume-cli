/**
 * ResumeAI Desktop - Settings View Controller
 */

class SettingsView {
    constructor(app) {
        this.app = app;
        this.storage = app.storage;
        this.api = app.api;
        this.toast = app.toast;
        this.utils = app.utils;
        
        this.init();
    }

    /**
     * Initialize settings view
     */
    init() {
        this.bindEvents();
        this.loadSettings();
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // API Settings form
        document.getElementById('apiSettingsForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveAPISettings();
        });

        document.getElementById('testApiConnection')?.addEventListener('click', () => {
            this.testAPIConnection();
        });

        // Toggle API key visibility
        document.getElementById('toggleAnthropicKey')?.addEventListener('click', () => {
            this.togglePasswordVisibility('anthropicKey');
        });

        document.getElementById('toggleOpenaiKey')?.addEventListener('click', () => {
            this.togglePasswordVisibility('openaiKey');
        });

        document.getElementById('toggleGithubToken')?.addEventListener('click', () => {
            this.togglePasswordVisibility('githubToken');
        });

        // GitHub Settings form
        document.getElementById('githubSettingsForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveGitHubSettings();
        });

        document.getElementById('syncGithub')?.addEventListener('click', () => {
            this.syncGitHub();
        });

        // App Settings form
        document.getElementById('appSettingsForm')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveAppSettings();
        });

        document.getElementById('browseOutputDir')?.addEventListener('click', () => {
            this.browseOutputDirectory();
        });

        document.getElementById('clearData')?.addEventListener('click', () => {
            this.clearAllData();
        });
    }

    /**
     * Load settings from storage
     */
    loadSettings() {
        const settings = this.storage.settings;

        // API Settings
        document.getElementById('aiProvider').value = settings.apiProvider || 'anthropic';
        document.getElementById('anthropicKey').value = settings.anthropicKey || '';
        document.getElementById('openaiKey').value = settings.openaiKey || '';
        document.getElementById('apiBaseUrl').value = settings.apiBaseUrl || '';

        // GitHub Settings
        document.getElementById('githubUsername').value = settings.githubUsername || '';
        document.getElementById('githubToken').value = settings.githubToken || '';
        document.getElementById('autoGithubProjects').checked = settings.autoGithubProjects || false;

        // App Settings
        document.getElementById('outputDirectory').value = settings.outputDirectory || '';
        document.getElementById('defaultVariant').value = settings.defaultVariant || 'v1.0.0-base';
        document.getElementById('enableTracking').checked = settings.enableTracking !== false;
        document.getElementById('enableNotifications').checked = settings.enableNotifications !== false;
        document.getElementById('autoSave').checked = settings.autoSave || false;
    }

    /**
     * Toggle password visibility
     */
    togglePasswordVisibility(inputId) {
        const input = document.getElementById(inputId);
        if (input.type === 'password') {
            input.type = 'text';
        } else {
            input.type = 'password';
        }
    }

    /**
     * Save API settings
     */
    saveAPISettings() {
        const settings = {
            apiProvider: document.getElementById('aiProvider').value,
            anthropicKey: document.getElementById('anthropicKey').value.trim(),
            openaiKey: document.getElementById('openaiKey').value.trim(),
            apiBaseUrl: document.getElementById('apiBaseUrl').value.trim(),
        };

        this.storage.saveSettings(settings);
        
        // Update API client
        if (this.api) {
            if (settings.apiBaseUrl) {
                this.api.baseURL = settings.apiBaseUrl;
            }
            // Set appropriate API key based on provider
            if (settings.apiProvider === 'anthropic') {
                this.api.setApiKey(settings.anthropicKey);
            } else {
                this.api.setApiKey(settings.openaiKey);
            }
        }

        this.toast.success('API settings saved');
    }

    /**
     * Test API connection
     */
    async testAPIConnection() {
        // First save settings
        this.saveAPISettings();

        const btn = document.getElementById('testApiConnection');
        const originalText = btn.textContent;
        btn.textContent = 'Testing...';
        btn.disabled = true;

        try {
            const result = await this.api.testConnection();
            
            if (result.connected) {
                this.toast.success(`Connected to ${result.url}`);
            } else {
                this.toast.warning(`Cannot connect: ${result.error || 'Unknown error'}`);
            }
        } catch (error) {
            this.toast.error(`Connection failed: ${error.message}`);
        } finally {
            btn.textContent = originalText;
            btn.disabled = false;
        }
    }

    /**
     * Save GitHub settings
     */
    saveGitHubSettings() {
        const settings = {
            githubUsername: document.getElementById('githubUsername').value.trim(),
            githubToken: document.getElementById('githubToken').value.trim(),
            autoGithubProjects: document.getElementById('autoGithubProjects').checked,
        };

        this.storage.saveSettings(settings);
        this.toast.success('GitHub settings saved');
    }

    /**
     * Sync GitHub projects
     */
    async syncGitHub() {
        const username = document.getElementById('githubUsername').value.trim();
        
        if (!username) {
            this.toast.error('Please enter your GitHub username first');
            return;
        }

        const btn = document.getElementById('syncGithub');
        const originalText = btn.textContent;
        btn.textContent = 'Syncing...';
        btn.disabled = true;

        try {
            // In a real implementation, this would call the GitHub sync API
            // For now, we'll just show a message
            await this.utils.delay(1000);
            this.toast.success(`GitHub sync initiated for ${username}`);
        } catch (error) {
            this.toast.error(`Sync failed: ${error.message}`);
        } finally {
            btn.textContent = originalText;
            btn.disabled = false;
        }
    }

    /**
     * Save application settings
     */
    saveAppSettings() {
        const settings = {
            outputDirectory: document.getElementById('outputDirectory').value.trim(),
            defaultVariant: document.getElementById('defaultVariant').value,
            enableTracking: document.getElementById('enableTracking').checked,
            enableNotifications: document.getElementById('enableNotifications').checked,
            autoSave: document.getElementById('autoSave').checked,
        };

        this.storage.saveSettings(settings);
        
        // Request notification permission if enabled
        if (settings.enableNotifications) {
            this.utils.requestNotificationPermission();
        }

        this.toast.success('Application settings saved');
    }

    /**
     * Browse output directory
     */
    browseOutputDirectory() {
        // In Tauri, this would open a folder picker dialog
        // For web version, we use a prompt
        this.app.modal.prompt({
            title: 'Output Directory',
            message: 'Enter the output directory path:',
            defaultValue: document.getElementById('outputDirectory').value,
        }).then((path) => {
            if (path) {
                document.getElementById('outputDirectory').value = path;
            }
        });
    }

    /**
     * Clear all data
     */
    async clearAllData() {
        const confirmed = await this.app.modal.confirm({
            title: 'Clear All Data',
            message: 'This will delete all applications, settings, and generated files. This action cannot be undone.',
            confirmText: 'Clear Everything',
            type: 'danger',
        });

        if (!confirmed) return;

        try {
            await this.storage.clearAllData();
            this.loadSettings();
            this.toast.success('All data cleared');
            
            // Refresh all views
            if (this.app.dashboard) this.app.dashboard.refresh();
            if (this.app.tracking) this.app.tracking.refresh();
            if (this.app.analytics) this.app.analytics.refresh();
        } catch (error) {
            console.error('Clear data error:', error);
            this.toast.error('Failed to clear data');
        }
    }

    /**
     * Export data
     */
    async exportData() {
        try {
            const data = await this.storage.exportData();
            const json = JSON.stringify(data, null, 2);
            const filename = `resumeai-backup-${new Date().toISOString().split('T')[0]}.json`;
            this.utils.downloadFile(json, filename, 'application/json');
            this.toast.success('Data exported successfully');
        } catch (error) {
            console.error('Export error:', error);
            this.toast.error('Failed to export data');
        }
    }

    /**
     * Import data
     */
    async importData() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';

        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            try {
                const content = await this.utils.readFileAsText(file);
                const data = JSON.parse(content);
                await this.storage.importData(data);
                this.loadSettings();
                this.toast.success('Data imported successfully');
                
                // Refresh all views
                if (this.app.dashboard) this.app.dashboard.refresh();
                if (this.app.tracking) this.app.tracking.refresh();
                if (this.app.analytics) this.app.analytics.refresh();
            } catch (error) {
                console.error('Import error:', error);
                this.toast.error(`Import failed: ${error.message}`);
            }
        };

        input.click();
    }
}

// Add delay helper to utils
if (!window.Utils.delay) {
    window.Utils.delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
}

// Export for use in other modules
window.SettingsView = SettingsView;
