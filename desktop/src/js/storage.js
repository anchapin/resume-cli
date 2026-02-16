/**
 * ResumeAI Desktop - Local Storage Manager
 * Handles persistent storage using localStorage and IndexedDB
 */

class StorageManager {
    constructor() {
        this.prefix = 'resumeai_';
        this.dbName = 'ResumeAI';
        this.dbVersion = 1;
        this.db = null;
    }

    /**
     * Initialize storage
     */
    async init() {
        await this.initIndexedDB();
        this.loadSettings();
    }

    /**
     * Initialize IndexedDB for larger data
     */
    initIndexedDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Create object stores
                if (!db.objectStoreNames.contains('applications')) {
                    const appStore = db.createObjectStore('applications', { keyPath: 'id', autoIncrement: true });
                    appStore.createIndex('company', 'company', { unique: false });
                    appStore.createIndex('status', 'status', { unique: false });
                    appStore.createIndex('date', 'date', { unique: false });
                }

                if (!db.objectStoreNames.contains('resumes')) {
                    db.createObjectStore('resumes', { keyPath: 'id' });
                }

                if (!db.objectStoreNames.contains('settings')) {
                    db.createObjectStore('settings', { keyPath: 'key' });
                }

                if (!db.objectStoreNames.contains('generatedFiles')) {
                    const fileStore = db.createObjectStore('generatedFiles', { keyPath: 'id', autoIncrement: true });
                    fileStore.createIndex('date', 'date', { unique: false });
                }
            };
        });
    }

    // =========================================================================
    // localStorage Methods (for settings and small data)
    // =========================================================================

    /**
     * Set item in localStorage
     */
    set(key, value) {
        try {
            localStorage.setItem(`${this.prefix}${key}`, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('Storage set error:', error);
            return false;
        }
    }

    /**
     * Get item from localStorage
     */
    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(`${this.prefix}${key}`);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Storage get error:', error);
            return defaultValue;
        }
    }

    /**
     * Remove item from localStorage
     */
    remove(key) {
        localStorage.removeItem(`${this.prefix}${key}`);
    }

    /**
     * Clear all items
     */
    clear() {
        const keys = Object.keys(localStorage);
        keys.forEach((key) => {
            if (key.startsWith(this.prefix)) {
                localStorage.removeItem(key);
            }
        });
    }

    // =========================================================================
    // Settings Methods
    // =========================================================================

    /**
     * Load settings from storage
     */
    loadSettings() {
        this.settings = {
            apiProvider: this.get('apiProvider', 'anthropic'),
            anthropicKey: this.get('anthropicKey', ''),
            openaiKey: this.get('openaiKey', ''),
            apiBaseUrl: this.get('apiBaseUrl', ''),
            githubUsername: this.get('githubUsername', ''),
            githubToken: this.get('githubToken', ''),
            autoGithubProjects: this.get('autoGithubProjects', false),
            outputDirectory: this.get('outputDirectory', ''),
            defaultVariant: this.get('defaultVariant', 'v1.0.0-base'),
            enableTracking: this.get('enableTracking', true),
            enableNotifications: this.get('enableNotifications', true),
            autoSave: this.get('autoSave', false),
            theme: this.get('theme', 'system'),
        };
        return this.settings;
    }

    /**
     * Save settings to storage
     */
    saveSettings(settings) {
        this.settings = { ...this.settings, ...settings };
        
        Object.entries(this.settings).forEach(([key, value]) => {
            this.set(key, value);
        });
        
        return this.settings;
    }

    /**
     * Get a specific setting
     */
    getSetting(key, defaultValue = null) {
        return this.settings[key] !== undefined ? this.settings[key] : defaultValue;
    }

    // =========================================================================
    // IndexedDB Methods (for larger data)
    // =========================================================================

    /**
     * Add item to IndexedDB store
     */
    async dbAdd(storeName, item) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.add(item);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Get item from IndexedDB store
     */
    async dbGet(storeName, key) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const request = store.get(key);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Update item in IndexedDB store
     */
    async dbUpdate(storeName, item) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.put(item);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Delete item from IndexedDB store
     */
    async dbDelete(storeName, key) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.delete(key);

            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Get all items from IndexedDB store
     */
    async dbGetAll(storeName) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const request = store.getAll();

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Query IndexedDB store by index
     */
    async dbQuery(storeName, indexName, value) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const index = store.index(indexName);
            const request = index.getAll(value);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    // =========================================================================
    // Application Tracking Methods
    // =========================================================================

    /**
     * Add job application
     */
    async addApplication(application) {
        const app = {
            ...application,
            date: application.date || new Date().toISOString(),
            updatedAt: new Date().toISOString(),
        };
        return this.dbAdd('applications', app);
    }

    /**
     * Get all applications
     */
    async getAllApplications() {
        const apps = await this.dbGetAll('applications');
        return apps.sort((a, b) => new Date(b.date) - new Date(a.date));
    }

    /**
     * Get applications by status
     */
    async getApplicationsByStatus(status) {
        return this.dbQuery('applications', 'status', status);
    }

    /**
     * Update application status
     */
    async updateApplicationStatus(id, status) {
        const app = await this.dbGet('applications', id);
        if (app) {
            app.status = status;
            app.updatedAt = new Date().toISOString();
            return this.dbUpdate('applications', app);
        }
        return null;
    }

    /**
     * Delete application
     */
    async deleteApplication(id) {
        return this.dbDelete('applications', id);
    }

    /**
     * Search applications
     */
    async searchApplications(query) {
        const apps = await this.getAllApplications();
        const lowerQuery = query.toLowerCase();
        return apps.filter(
            (app) =>
                app.company.toLowerCase().includes(lowerQuery) ||
                (app.role && app.role.toLowerCase().includes(lowerQuery)) ||
                (app.notes && app.notes.toLowerCase().includes(lowerQuery))
        );
    }

    // =========================================================================
    // Resume Methods
    // =========================================================================

    /**
     * Save resume content
     */
    async saveResume(id, content, filePath = null) {
        const resume = {
            id,
            content,
            filePath,
            updatedAt: new Date().toISOString(),
        };
        return this.dbUpdate('resumes', resume);
    }

    /**
     * Get resume content
     */
    async getResume(id = 'default') {
        return this.dbGet('resumes', id);
    }

    // =========================================================================
    // Generated Files Methods
    // =========================================================================

    /**
     * Save generated file record
     */
    async saveGeneratedFile(file) {
        const record = {
            ...file,
            date: new Date().toISOString(),
        };
        return this.dbAdd('generatedFiles', record);
    }

    /**
     * Get all generated files
     */
    async getAllGeneratedFiles() {
        const files = await this.dbGetAll('generatedFiles');
        return files.sort((a, b) => new Date(b.date) - new Date(a.date));
    }

    // =========================================================================
    // Export/Import Methods
    // =========================================================================

    /**
     * Export all data as JSON
     */
    async exportData() {
        const applications = await this.getAllApplications();
        const generatedFiles = await this.getAllGeneratedFiles();
        
        return {
            version: 1,
            exportDate: new Date().toISOString(),
            settings: this.settings,
            applications,
            generatedFiles,
        };
    }

    /**
     * Import data from JSON
     */
    async importData(data) {
        if (!data.version || data.version !== 1) {
            throw new Error('Invalid data format');
        }

        // Import settings
        if (data.settings) {
            this.saveSettings(data.settings);
        }

        // Import applications
        if (data.applications) {
            for (const app of data.applications) {
                await this.dbAdd('applications', app);
            }
        }

        // Import generated files
        if (data.generatedFiles) {
            for (const file of data.generatedFiles) {
                await this.dbAdd('generatedFiles', file);
            }
        }

        return true;
    }

    /**
     * Clear all data
     */
    async clearAllData() {
        this.clear();
        
        // Clear IndexedDB stores
        const stores = ['applications', 'resumes', 'generatedFiles'];
        for (const storeName of stores) {
            const store = this.db.transaction(storeName, 'readwrite').objectStore(storeName);
            await store.clear();
        }
        
        // Reload settings (will be defaults)
        this.loadSettings();
    }
}

// Export for use in other modules
window.StorageManager = StorageManager;
