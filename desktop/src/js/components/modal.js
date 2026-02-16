/**
 * ResumeAI Desktop - Modal Dialog Component
 */

class ModalManager {
    constructor() {
        this.overlay = document.getElementById('modalOverlay');
        this.modal = document.getElementById('modalContent');
        this.titleEl = document.getElementById('modalTitle');
        this.bodyEl = document.getElementById('modalBody');
        this.footerEl = document.getElementById('modalFooter');
        this.closeBtn = document.getElementById('modalClose');
        
        this.isOpen = false;
        this.onClose = null;
        
        this.init();
    }

    /**
     * Initialize modal event listeners
     */
    init() {
        // Close button
        this.closeBtn.addEventListener('click', () => this.close());
        
        // Overlay click
        this.overlay.addEventListener('click', (e) => {
            if (e.target === this.overlay) {
                this.close();
            }
        });
        
        // Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });
    }

    /**
     * Open modal with content
     */
    open(options = {}) {
        const {
            title = 'Modal',
            content = '',
            buttons = [],
            onClose = null,
            size = 'medium',
        } = options;

        this.titleEl.textContent = title;
        this.bodyEl.innerHTML = content;
        
        // Build footer buttons
        this.footerEl.innerHTML = '';
        buttons.forEach((btn) => {
            const button = document.createElement('button');
            button.className = `btn ${btn.class || ''}`;
            button.textContent = btn.text;
            button.addEventListener('click', () => {
                if (btn.onClick) {
                    btn.onClick();
                }
                if (btn.close !== false) {
                    this.close();
                }
            });
            this.footerEl.appendChild(button);
        });

        // Set size class
        this.modal.className = 'modal';
        if (size === 'small') {
            this.modal.style.maxWidth = '400px';
        } else if (size === 'large') {
            this.modal.style.maxWidth = '700px';
        } else {
            this.modal.style.maxWidth = '500px';
        }

        // Show modal
        this.overlay.classList.remove('hidden');
        this.isOpen = true;
        this.onClose = onClose;
        
        // Focus first button or close button
        const firstButton = this.footerEl.querySelector('button');
        if (firstButton) {
            firstButton.focus();
        }
    }

    /**
     * Close modal
     */
    close() {
        if (!this.isOpen) return;
        
        this.overlay.classList.add('hidden');
        this.isOpen = false;
        
        if (this.onClose) {
            this.onClose();
        }
    }

    /**
     * Show confirmation dialog
     */
    confirm(options = {}) {
        return new Promise((resolve) => {
            const {
                title = 'Confirm',
                message = 'Are you sure?',
                confirmText = 'Confirm',
                cancelText = 'Cancel',
                type = 'warning',
            } = options;

            this.open({
                title,
                content: `<p>${message}</p>`,
                buttons: [
                    {
                        text: cancelText,
                        class: 'btn',
                        onClick: () => resolve(false),
                    },
                    {
                        text: confirmText,
                        class: type === 'danger' ? 'btn btn-danger' : 'btn btn-primary',
                        onClick: () => resolve(true),
                    },
                ],
                onClose: () => resolve(false),
            });
        });
    }

    /**
     * Show alert dialog
     */
    alert(options = {}) {
        return new Promise((resolve) => {
            const {
                title = 'Alert',
                message = '',
                okText = 'OK',
                type = 'info',
            } = options;

            this.open({
                title,
                content: `<p>${message}</p>`,
                buttons: [
                    {
                        text: okText,
                        class: type === 'danger' ? 'btn btn-danger' : 'btn btn-primary',
                        onClick: () => resolve(),
                    },
                ],
            });
        });
    }

    /**
     * Show prompt dialog
     */
    prompt(options = {}) {
        return new Promise((resolve) => {
            const {
                title = 'Input',
                message = '',
                defaultValue = '',
                placeholder = '',
                confirmText = 'OK',
                cancelText = 'Cancel',
                type = 'text',
            } = options;

            let inputValue = defaultValue;

            this.open({
                title,
                content: `
                    ${message ? `<p>${message}</p>` : ''}
                    <input type="${type}" 
                           class="input" 
                           style="width: 100%; margin-top: 1rem;"
                           value="${Utils.escapeHTML(defaultValue)}"
                           placeholder="${Utils.escapeHTML(placeholder)}"
                           id="modalPromptInput"
                    />
                `,
                buttons: [
                    {
                        text: cancelText,
                        class: 'btn',
                        onClick: () => resolve(null),
                    },
                    {
                        text: confirmText,
                        class: 'btn btn-primary',
                        onClick: () => {
                            const input = document.getElementById('modalPromptInput');
                            resolve(input ? input.value : null);
                        },
                    },
                ],
                onClose: () => resolve(null),
            });

            // Focus input after modal opens
            setTimeout(() => {
                const input = document.getElementById('modalPromptInput');
                if (input) {
                    input.focus();
                    input.select();
                }
            }, 100);
        });
    }

    /**
     * Update modal content
     */
    updateContent(content) {
        this.bodyEl.innerHTML = content;
    }

    /**
     * Set loading state
     */
    setLoading(loading = true, message = 'Loading...') {
        if (loading) {
            this.bodyEl.innerHTML = `
                <div class="loading-state">
                    <div class="spinner"></div>
                    <p>${message}</p>
                </div>
            `;
        }
    }
}

// Add loading styles
const style = document.createElement('style');
style.textContent = `
    .loading-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        gap: 1rem;
    }
    
    .spinner {
        width: 40px;
        height: 40px;
        border: 4px solid var(--border-color);
        border-top-color: var(--primary);
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);

// Export for use in other modules
window.ModalManager = ModalManager;
