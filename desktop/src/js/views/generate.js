/**
 * ResumeAI Desktop - Generate View Controller
 */

class GenerateView {
    constructor(app) {
        this.app = app;
        this.storage = app.storage;
        this.api = app.api;
        this.toast = app.toast;
        this.utils = app.utils;
        
        this.jobDescription = '';
        this.isGenerating = false;
        
        this.init();
    }

    /**
     * Initialize generate view
     */
    init() {
        this.bindEvents();
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // File upload area
        const uploadArea = document.getElementById('jobDescUpload');
        const fileInput = document.getElementById('jobDescFile');
        
        uploadArea?.addEventListener('click', () => fileInput?.click());
        
        fileInput?.addEventListener('change', (e) => {
            this.handleFileSelect(e);
        });

        // Drag and drop
        uploadArea?.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea?.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea?.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file) {
                this.handleFileSelect({ target: { files: [file] } });
            }
        });

        // Remove job description
        document.getElementById('removeJobDesc')?.addEventListener('click', () => {
            this.clearJobDescription();
        });

        // Job description text area
        document.getElementById('jobDescText')?.addEventListener('input', (e) => {
            this.jobDescription = e.target.value;
        });

        // Generate button
        document.getElementById('generateResume')?.addEventListener('click', () => {
            this.generate();
        });

        // Open output folder
        document.getElementById('openOutputFolder')?.addEventListener('click', () => {
            this.openOutputFolder();
        });
    }

    /**
     * Handle file selection
     */
    async handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;

        try {
            const content = await this.utils.readFileAsText(file);
            this.jobDescription = content;
            
            // Update UI
            document.getElementById('jobDescFileName').textContent = file.name;
            document.getElementById('jobDescUpload').classList.add('hidden');
            document.getElementById('jobDescContent').classList.remove('hidden');
            document.getElementById('jobDescText').value = content;
            
            this.toast.success(`Loaded ${file.name}`);
        } catch (error) {
            console.error('File read error:', error);
            this.toast.error('Failed to read file');
        }
    }

    /**
     * Clear job description
     */
    clearJobDescription() {
        this.jobDescription = '';
        document.getElementById('jobDescUpload').classList.remove('hidden');
        document.getElementById('jobDescContent').classList.add('hidden');
        document.getElementById('jobDescFile').value = '';
        document.getElementById('jobDescText').value = '';
    }

    /**
     * Generate resume and cover letter
     */
    async generate() {
        if (this.isGenerating) return;

        // Validate inputs
        const resumeData = await this.storage.getResume('default');
        if (!resumeData || !resumeData.content) {
            this.toast.error('Please load resume.yaml first');
            this.app.navigate('resume');
            return;
        }

        if (!this.jobDescription.trim()) {
            this.toast.error('Please provide a job description');
            return;
        }

        this.isGenerating = true;
        this.showProgress();

        try {
            // Parse resume YAML
            let resumeYaml;
            try {
                // In a real implementation, use a proper YAML parser
                resumeYaml = this.utils.parseSimpleYAML(resumeData.content);
            } catch (error) {
                throw new Error('Invalid YAML in resume.yaml');
            }

            // Get generation options
            const variant = document.getElementById('generateVariant').value;
            const format = document.getElementById('generateFormat').value;
            const template = document.getElementById('generateTemplate').value;
            const useAI = document.getElementById('useAI').checked;
            const includeCoverLetter = document.getElementById('includeCoverLetter').checked;
            const includeGithubProjects = document.getElementById('includeGithubProjects').checked;

            // Step 1: Extract job requirements
            this.updateProgress('step-extract', 'active');
            await this.delay(500);
            
            // Extract company name and job title
            const companyName = this.utils.extractCompanyName(this.jobDescription);
            const jobTitle = this.utils.extractJobTitle(this.jobDescription);

            // Step 2: Generate resume
            this.updateProgress('step-resume', 'active');
            this.updateProgress('step-extract', 'completed');
            await this.delay(500);

            let resumeContent = resumeData.content;
            
            if (useAI && this.api) {
                try {
                    const tailoredData = await this.api.tailorResume(resumeYaml, this.jobDescription);
                    // In a real implementation, convert tailoredData back to YAML
                    resumeContent = JSON.stringify(tailoredData, null, 2);
                } catch (error) {
                    console.warn('AI tailoring failed, using original resume');
                }
            }

            // Step 3: Generate cover letter
            if (includeCoverLetter) {
                this.updateProgress('step-cover', 'active');
                this.updateProgress('step-resume', 'completed');
                await this.delay(500);

                if (useAI && this.api) {
                    try {
                        const coverLetter = await this.api.generateCoverLetter(
                            resumeYaml,
                            this.jobDescription,
                            companyName,
                            variant,
                            'md'
                        );
                        // Store cover letter content
                        this.coverLetterContent = coverLetter.content;
                    } catch (error) {
                        console.warn('Cover letter generation failed');
                    }
                }
            }

            // Step 4: Compile PDF
            this.updateProgress('step-pdf', 'active');
            if (includeCoverLetter) {
                this.updateProgress('step-cover', 'completed');
            } else {
                this.updateProgress('step-resume', 'completed');
            }
            await this.delay(500);

            // Generate output files
            const dateStr = new Date().toISOString().split('T')[0];
            const companySlug = companyName.toLowerCase().replace(/[^a-z0-9]+/g, '-').slice(0, 30);
            const outputDir = `${companySlug}-${dateStr}`;

            const generatedFiles = [];

            // Resume files
            generatedFiles.push({
                name: `resume.md`,
                path: `${outputDir}/resume.md`,
                content: resumeContent,
                type: 'resume',
            });

            if (format === 'pdf' || format === 'tex') {
                generatedFiles.push({
                    name: `resume.${format}`,
                    path: `${outputDir}/resume.${format}`,
                    content: resumeContent,
                    type: 'resume',
                });
            }

            // Cover letter files
            if (includeCoverLetter && this.coverLetterContent) {
                generatedFiles.push({
                    name: `cover-letter.md`,
                    path: `${outputDir}/cover-letter.md`,
                    content: this.coverLetterContent,
                    type: 'cover-letter',
                });

                generatedFiles.push({
                    name: `cover-letter.pdf`,
                    path: `${outputDir}/cover-letter.pdf`,
                    content: this.coverLetterContent,
                    type: 'cover-letter',
                });
            }

            // Save generated files
            for (const file of generatedFiles) {
                await this.storage.saveGeneratedFile(file);
            }

            // Update progress
            this.updateProgress('step-pdf', 'completed');
            this.updateProgress(100);

            // Show results
            this.showResults(generatedFiles, outputDir);
            
            this.toast.success('Application package generated!');

        } catch (error) {
            console.error('Generate error:', error);
            this.toast.error(`Generation failed: ${error.message}`);
            this.hideProgress();
        } finally {
            this.isGenerating = false;
        }
    }

    /**
     * Show progress panel
     */
    showProgress() {
        document.getElementById('progressPanel').classList.remove('hidden');
        document.getElementById('resultsPanel').classList.add('hidden');
        this.updateProgress(0);
        
        // Reset all steps
        ['step-extract', 'step-resume', 'step-cover', 'step-pdf'].forEach((step) => {
            document.getElementById(step).className = 'progress-step';
        });
    }

    /**
     * Hide progress panel
     */
    hideProgress() {
        document.getElementById('progressPanel').classList.add('hidden');
    }

    /**
     * Update progress indicator
     */
    updateProgress(stepOrPercent, status = '') {
        if (typeof stepOrPercent === 'number') {
            // Update progress bar percentage
            document.getElementById('progressFill').style.width = `${stepOrPercent}%`;
        } else {
            // Update specific step status
            const stepEl = document.getElementById(stepOrPercent);
            if (stepEl) {
                stepEl.className = `progress-step ${status}`;
                
                // Update indicator icon
                const indicator = stepEl.querySelector('.step-indicator');
                if (status === 'active') {
                    indicator.textContent = '⏳';
                } else if (status === 'completed') {
                    indicator.textContent = '✓';
                } else {
                    indicator.textContent = '⏳';
                }
            }
        }
    }

    /**
     * Show results panel
     */
    showResults(files, outputDir) {
        const container = document.getElementById('generatedFiles');
        
        container.innerHTML = files
            .map(
                (file) => `
                <div class="generated-file">
                    <span class="generated-file-name">
                        ${file.type === 'resume' ? '📄' : '✉️'}
                        ${file.name}
                    </span>
                    <button class="btn btn-sm" onclick="app.downloadFile('${file.path}')">
                        Download
                    </button>
                </div>
            `
            )
            .join('');

        document.getElementById('progressPanel').classList.add('hidden');
        document.getElementById('resultsPanel').classList.remove('hidden');
        
        // Store current output dir
        this.currentOutputDir = outputDir;
    }

    /**
     * Open output folder
     */
    openOutputFolder() {
        // In Tauri, this would open the actual folder
        // For web version, we show a message
        this.toast.info(`Output directory: ${this.currentOutputDir || 'output/'}`);
    }

    /**
     * Download a generated file
     */
    downloadFile(path) {
        // Find the file in storage
        this.storage.getAllGeneratedFiles().then((files) => {
            const file = files.find((f) => f.path === path);
            if (file && file.content) {
                const ext = path.split('.').pop();
                const mimeType = ext === 'pdf' ? 'application/pdf' : 'text/plain';
                this.utils.downloadFile(file.content, file.name, mimeType);
            }
        });
    }

    /**
     * Delay helper
     */
    delay(ms) {
        return new Promise((resolve) => setTimeout(resolve, ms));
    }
}

// Export for use in other modules
window.GenerateView = GenerateView;
