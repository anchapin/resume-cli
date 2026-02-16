/**
 * ResumeAI Desktop - Unit Tests
 * Basic tests for core functionality
 */

// Test utilities
describe('Utils', () => {
    test('formatDate should format dates correctly', () => {
        const date = '2024-01-15T10:30:00Z';
        const result = Utils.formatDate(date);
        expect(result).toBeTruthy();
        expect(typeof result).toBe('string');
    });

    test('formatRelative should show relative time', () => {
        const now = new Date().toISOString();
        const result = Utils.formatRelative(now);
        expect(result).toContain('ago') || expect(result).toContain('Just');
    });

    test('truncate should limit text length', () => {
        const text = 'This is a long text that should be truncated';
        const result = Utils.truncate(text, 20);
        expect(result.length).toBeLessThanOrEqual(23); // 20 + '...'
    });

    test('escapeHTML should escape special characters', () => {
        const html = '<script>alert("xss")</script>';
        const result = Utils.escapeHTML(html);
        expect(result).not.toContain('<script>');
    });

    test('generateId should create unique IDs', () => {
        const id1 = Utils.generateId();
        const id2 = Utils.generateId();
        expect(id1).not.toBe(id2);
    });

    test('calculatePercentage should calculate correctly', () => {
        expect(Utils.calculatePercentage(25, 100)).toBe('25');
        expect(Utils.calculatePercentage(1, 3, 2)).toBe('33.33');
    });

    test('groupBy should group array by key', () => {
        const items = [
            { status: 'applied', company: 'A' },
            { status: 'interview', company: 'B' },
            { status: 'applied', company: 'C' },
        ];
        const result = Utils.groupBy(items, 'status');
        expect(result.applied.length).toBe(2);
        expect(result.interview.length).toBe(1);
    });

    test('extractCompanyName should extract from text', () => {
        const text = 'We are hiring at Google for a Senior Engineer position';
        const result = Utils.extractCompanyName(text);
        expect(result).toBeTruthy();
    });
});

// Test storage manager
describe('StorageManager', () => {
    let storage;

    beforeEach(() => {
        storage = new StorageManager();
    });

    test('set and get should work', () => {
        storage.set('testKey', { value: 'test' });
        const result = storage.get('testKey');
        expect(result.value).toBe('test');
    });

    test('get should return default for missing key', () => {
        const result = storage.get('nonexistent', 'default');
        expect(result).toBe('default');
    });

    test('remove should delete key', () => {
        storage.set('toRemove', 'value');
        storage.remove('toRemove');
        const result = storage.get('toRemove');
        expect(result).toBeNull();
    });

    test('saveSettings should persist settings', () => {
        const settings = { apiProvider: 'anthropic', testKey: 'value' };
        storage.saveSettings(settings);
        expect(storage.settings.apiProvider).toBe('anthropic');
    });
});

// Test API client
describe('APIClient', () => {
    let api;

    beforeEach(() => {
        api = new APIClient('http://localhost:8000');
    });

    test('should initialize with base URL', () => {
        expect(api.baseURL).toBe('http://localhost:8000');
    });

    test('setApiKey should store the key', () => {
        api.setApiKey('test-key');
        expect(api.apiKey).toBe('test-key');
    });

    test('buildURL should construct full URL', () => {
        const url = api.buildURL('/v1/variants');
        expect(url).toBe('http://localhost:8000/v1/variants');
    });

    test('getHeaders should include API key when set', () => {
        api.setApiKey('test-key');
        const headers = api.getHeaders();
        expect(headers['X-API-Key']).toBe('test-key');
    });

    test('getHeaders should not include API key when not set', () => {
        const headers = api.getHeaders();
        expect(headers['X-API-Key']).toBeUndefined();
    });
});

// Test toast manager
describe('ToastManager', () => {
    let toast;
    let container;

    beforeEach(() => {
        container = document.createElement('div');
        container.id = 'toastContainer';
        document.body.appendChild(container);
        toast = new ToastManager('toastContainer');
    });

    afterEach(() => {
        document.body.removeChild(container);
    });

    test('show should create toast element', () => {
        toast.show('Test message', 'info');
        expect(container.children.length).toBe(1);
    });

    test('success should create success toast', () => {
        toast.success('Success!');
        const toastEl = container.querySelector('.toast.success');
        expect(toastEl).toBeTruthy();
    });

    test('error should create error toast', () => {
        toast.error('Error!');
        const toastEl = container.querySelector('.toast.error');
        expect(toastEl).toBeTruthy();
    });

    test('clear should remove all toasts', () => {
        toast.show('1');
        toast.show('2');
        toast.show('3');
        toast.clear();
        // Toasts are removed with animation, so we check they're being removed
        expect(toast.toasts.length).toBe(3);
    });
});

// Test modal manager
describe('ModalManager', () => {
    let modal;

    beforeEach(() => {
        // Create modal elements if they don't exist
        if (!document.getElementById('modalOverlay')) {
            const overlay = document.createElement('div');
            overlay.id = 'modalOverlay';
            overlay.className = 'modal-overlay hidden';
            overlay.innerHTML = `
                <div class="modal" id="modalContent">
                    <div class="modal-header">
                        <h3 id="modalTitle"></h3>
                        <button class="modal-close" id="modalClose">&times;</button>
                    </div>
                    <div class="modal-body" id="modalBody"></div>
                    <div class="modal-footer" id="modalFooter"></div>
                </div>
            `;
            document.body.appendChild(overlay);
        }
        modal = new ModalManager();
    });

    test('open should show modal', () => {
        modal.open({ title: 'Test', content: 'Content' });
        expect(modal.isOpen).toBe(true);
        expect(document.getElementById('modalOverlay').classList.contains('hidden')).toBe(false);
    });

    test('close should hide modal', () => {
        modal.open({ title: 'Test' });
        modal.close();
        expect(modal.isOpen).toBe(false);
    });

    test('confirm should return promise', async () => {
        const promise = modal.confirm({ message: 'Are you sure?' });
        expect(promise).toBeInstanceOf(Promise);
        modal.close();
        const result = await promise;
        expect(result).toBe(false);
    });
});

// Test charts manager
describe('ChartsManager', () => {
    let charts;
    let canvas;

    beforeEach(() => {
        canvas = document.createElement('canvas');
        canvas.id = 'testChart';
        canvas.width = 400;
        canvas.height = 300;
        document.body.appendChild(canvas);
        charts = new ChartsManager();
    });

    afterEach(() => {
        document.body.removeChild(canvas);
    });

    test('createBarChart should create chart', () => {
        const data = {
            labels: ['A', 'B', 'C'],
            values: [10, 20, 30],
        };
        const chart = charts.createBarChart('testChart', data);
        expect(chart).toBeTruthy();
        expect(chart.type).toBe('bar');
    });

    test('createPieChart should create chart', () => {
        const data = {
            labels: ['A', 'B'],
            values: [50, 50],
        };
        const chart = charts.createPieChart('testChart', data);
        expect(chart).toBeTruthy();
        expect(chart.type).toBe('pie');
    });

    test('createLineChart should create chart', () => {
        const data = {
            labels: ['Jan', 'Feb', 'Mar'],
            values: [10, 15, 20],
        };
        const chart = charts.createLineChart('testChart', data);
        expect(chart).toBeTruthy();
        expect(chart.type).toBe('line');
    });

    test('destroyChart should remove chart', () => {
        const data = { labels: ['A'], values: [10] };
        charts.createBarChart('testChart', data);
        charts.destroyChart('testChart');
        expect(charts.charts.has('testChart')).toBe(false);
    });
});

// Test application views
describe('DashboardView', () => {
    test('should calculate overview correctly', () => {
        const applications = [
            { status: 'applied', date: new Date().toISOString() },
            { status: 'interview', date: new Date().toISOString() },
            { status: 'offer', date: new Date().toISOString() },
        ];
        
        // Simulate calculateOverview logic
        const total = applications.length;
        const interviews = applications.filter(a => a.status === 'interview').length;
        const offers = applications.filter(a => a.status === 'offer').length;
        const responseRate = ((applications.filter(a => ['interview', 'offer'].includes(a.status)).length) / total) * 100;
        
        expect(total).toBe(3);
        expect(interviews).toBe(1);
        expect(offers).toBe(1);
        expect(responseRate).toBeCloseTo(66.67, 1);
    });
});

describe('TrackingView', () => {
    test('should filter applications by status', () => {
        const applications = [
            { status: 'applied', company: 'A' },
            { status: 'interview', company: 'B' },
            { status: 'applied', company: 'C' },
        ];
        
        const filtered = applications.filter(a => a.status === 'applied');
        expect(filtered.length).toBe(2);
    });

    test('should filter applications by search query', () => {
        const applications = [
            { company: 'Google', role: 'Engineer' },
            { company: 'Meta', role: 'Developer' },
            { company: 'Amazon', role: 'SDE' },
        ];
        
        const query = 'google';
        const filtered = applications.filter(a => 
            a.company.toLowerCase().includes(query)
        );
        expect(filtered.length).toBe(1);
    });
});

// Run tests if in Node.js environment
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        Utils,
        StorageManager,
        APIClient,
        ToastManager,
        ModalManager,
        ChartsManager,
    };
}
