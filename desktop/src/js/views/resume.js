/**
 * ResumeAI Desktop - Resume Management View Controller
 */

class ResumeView {
    constructor(app) {
        this.app = app;
        this.storage = app.storage;
        this.api = app.api;
        this.toast = app.toast;
        this.utils = app.utils;
        
        this.currentFile = null;
        this.currentContent = '';
        this.isDirty = false;
        
        this.init();
    }

    /**
     * Initialize resume view
     */
    init() {
        this.bindEvents();
        this.loadSavedResume();
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // File operations
        document.getElementById('openResumeFile')?.addEventListener('click', () => {
            this.openFile();
        });

        document.getElementById('saveResumeFile')?.addEventListener('click', () => {
            this.saveFile();
        });

        // Editor operations
        document.getElementById('yamlEditor')?.addEventListener('input', () => {
            this.isDirty = true;
            this.hideValidation();
        });

        document.getElementById('validateYaml')?.addEventListener('click', () => {
            this.validateYaml();
        });

        document.getElementById('formatYaml')?.addEventListener('click', () => {
            this.formatYaml();
        });

        // Preview
        document.getElementById('refreshPreview')?.addEventListener('click', () => {
            this.updatePreview();
        });

        document.getElementById('previewVariant')?.addEventListener('change', () => {
            this.updatePreview();
        });

        // Warn before leaving with unsaved changes
        window.addEventListener('beforeunload', (e) => {
            if (this.isDirty) {
                e.preventDefault();
                e.returnValue = '';
            }
        });
    }

    /**
     * Load saved resume from storage
     */
    async loadSavedResume() {
        try {
            const resume = await this.storage.getResume('default');
            if (resume && resume.content) {
                this.currentContent = resume.content;
                document.getElementById('yamlEditor').value = resume.content;
                document.getElementById('currentFilePath').textContent = resume.filePath || 'Local storage';
                this.isDirty = false;
                this.updatePreview();
            }
        } catch (error) {
            console.error('Load resume error:', error);
        }
    }

    /**
     * Open resume file
     */
    async openFile() {
        try {
            // In Tauri, this would use the file dialog API
            // For web version, we use a file input
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.yaml,.yml,.txt';
            
            input.onchange = async (e) => {
                const file = e.target.files[0];
                if (file) {
                    const content = await this.utils.readFileAsText(file);
                    this.currentContent = content;
                    this.currentFile = file;
                    document.getElementById('yamlEditor').value = content;
                    document.getElementById('currentFilePath').textContent = file.name;
                    this.isDirty = false;
                    
                    // Save to storage
                    await this.storage.saveResume('default', content, file.name);
                    
                    this.toast.success(`Loaded ${file.name}`);
                    this.updatePreview();
                }
            };
            
            input.click();
        } catch (error) {
            console.error('Open file error:', error);
            this.toast.error('Failed to open file');
        }
    }

    /**
     * Save resume file
     */
    async saveFile() {
        try {
            const content = document.getElementById('yamlEditor').value;
            this.currentContent = content;
            
            // Save to storage
            await this.storage.saveResume('default', content, this.currentFile?.name || 'resume.yaml');
            
            // In Tauri, we could write directly to the file system
            // For web version, we download the file
            if (this.currentFile) {
                this.utils.downloadFile(content, this.currentFile.name, 'text/yaml');
            } else {
                this.utils.downloadFile(content, 'resume.yaml', 'text/yaml');
            }
            
            this.isDirty = false;
            this.toast.success('Resume saved');
        } catch (error) {
            console.error('Save file error:', error);
            this.toast.error('Failed to save file');
        }
    }

    /**
     * Validate YAML content
     */
    async validateYaml() {
        const content = document.getElementById('yamlEditor').value;
        const validationEl = document.getElementById('yamlValidation');
        
        try {
            // Basic YAML validation
            if (!content.trim()) {
                throw new Error('YAML content is empty');
            }

            // Check for basic YAML structure
            const lines = content.split('\n');
            let hasContent = false;
            let indentError = false;
            let prevIndent = 0;

            for (let i = 0; i < lines.length; i++) {
                const line = lines[i];
                
                // Skip empty lines and comments
                if (!line.trim() || line.trim().startsWith('#')) continue;
                
                hasContent = true;
                
                // Check indentation (should be spaces, not tabs)
                if (line.startsWith('\t')) {
                    indentError = true;
                    break;
                }
                
                // Check for consistent indentation
                const indent = line.search(/\S/);
                if (indent % 2 !== 0 && indent > 0) {
                    // YAML typically uses 2-space indentation
                    console.warn(`Line ${i + 1}: Odd indentation (${indent} spaces)`);
                }
            }

            if (!hasContent) {
                throw new Error('No valid YAML content found');
            }

            if (indentError) {
                throw new Error('Tabs detected. YAML requires spaces for indentation.');
            }

            // Check for required sections
            const requiredSections = ['contact', 'experience', 'skills', 'education'];
            const missingSections = [];
            
            requiredSections.forEach((section) => {
                if (!content.includes(`${section}:`)) {
                    missingSections.push(section);
                }
            });

            // Show validation result
            validationEl.className = 'validation-status success';
            let message = '✓ YAML syntax appears valid';
            if (missingSections.length > 0) {
                message += `<br><small>Warning: Missing recommended sections: ${missingSections.join(', ')}</small>`;
            }
            validationEl.innerHTML = message;
            validationEl.classList.remove('hidden');
            
            this.toast.success('YAML validation passed');
            
        } catch (error) {
            validationEl.className = 'validation-status error';
            validationEl.innerHTML = `✕ ${this.utils.escapeHTML(error.message)}`;
            validationEl.classList.remove('hidden');
            this.toast.error(`Validation failed: ${error.message}`);
        }
    }

    /**
     * Hide validation status
     */
    hideValidation() {
        document.getElementById('yamlValidation').classList.add('hidden');
    }

    /**
     * Format YAML content
     */
    formatYaml() {
        const editor = document.getElementById('yamlEditor');
        let content = editor.value;
        
        try {
            // Basic formatting
            // Replace tabs with spaces
            content = content.replace(/\t/g, '  ');
            
            // Remove trailing whitespace
            content = content.split('\n').map((line) => line.trimEnd()).join('\n');
            
            // Ensure proper line endings
            content = content.replace(/\r\n/g, '\n');
            
            editor.value = content;
            this.isDirty = true;
            
            this.toast.success('YAML formatted');
        } catch (error) {
            console.error('Format error:', error);
            this.toast.error('Failed to format YAML');
        }
    }

    /**
     * Update preview panel
     */
    async updatePreview() {
        const content = document.getElementById('yamlEditor').value;
        const variant = document.getElementById('previewVariant').value;
        const previewEl = document.getElementById('previewContent');
        
        if (!content.trim()) {
            previewEl.innerHTML = '<p class="text-muted">Load resume.yaml to preview</p>';
            return;
        }

        try {
            // Parse and display a simple preview
            const parsed = this.utils.parseSimpleYAML(content);
            
            let html = '<div class="preview-section">';
            
            // Contact info
            if (parsed.contact) {
                html += `
                    <h3>Contact</h3>
                    <p><strong>Name:</strong> ${parsed.contact.name || 'N/A'}</p>
                    <p><strong>Email:</strong> ${parsed.contact.email || 'N/A'}</p>
                    <p><strong>Phone:</strong> ${parsed.contact.phone || 'N/A'}</p>
                `;
            }
            
            // Professional summary
            if (parsed.professional_summary) {
                html += `
                    <h3>Summary</h3>
                    <p>${this.utils.truncate(parsed.professional_summary.base || parsed.professional_summary, 200)}</p>
                `;
            }
            
            // Skills
            if (parsed.skills) {
                html += '<h3>Skills</h3><ul>';
                Object.entries(parsed.skills).forEach(([category, items]) => {
                    if (Array.isArray(items)) {
                        html += `<li><strong>${category}:</strong> ${items.length} items</li>`;
                    }
                });
                html += '</ul>';
            }
            
            // Experience
            if (parsed.experience && Array.isArray(parsed.experience)) {
                html += `
                    <h3>Experience</h3>
                    <p>${parsed.experience.length} positions</p>
                    <ul>
                `;
                parsed.experience.slice(0, 3).forEach((exp) => {
                    html += `<li>${exp.company || 'Unknown'} - ${exp.title || 'Unknown'}</li>`;
                });
                if (parsed.experience.length > 3) {
                    html += `<li>... and ${parsed.experience.length - 3} more</li>`;
                }
                html += '</ul>';
            }
            
            html += '</div>';
            
            previewEl.innerHTML = html;
            
        } catch (error) {
            console.error('Preview error:', error);
            previewEl.innerHTML = `<p class="text-muted">Unable to generate preview: ${error.message}</p>`;
        }
    }
}

// Export for use in other modules
window.ResumeView = ResumeView;
