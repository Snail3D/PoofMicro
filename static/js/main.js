// PoofMicro ESP32 Builder - Main Application

class PoofMicroApp {
    constructor() {
        this.apiBase = '/api';
        this.selectedLibraries = [];
        this.selectedMaterials = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadProjects();
    }

    setupEventListeners() {
        // Project form
        const projectForm = document.getElementById('projectForm');
        projectForm.addEventListener('submit', (e) => this.handleBuildProject(e));

        // Search buttons
        document.getElementById('librarySearchBtn').addEventListener('click', () => this.searchLibraries());
        document.getElementById('materialSearchBtn').addEventListener('click', () => this.searchMaterials());

        // Enter key for searches
        document.getElementById('librarySearch').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.searchLibraries();
        });
        document.getElementById('materialSearch').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.searchMaterials();
        });

        // Settings modal
        document.getElementById('settingsBtn').addEventListener('click', () => this.openSettings());
        document.getElementById('closeSettings').addEventListener('click', () => this.closeSettings());
        document.getElementById('saveSettings').addEventListener('click', () => this.saveSettings());

        // Close modal on backdrop click
        document.getElementById('settingsModal').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) this.closeSettings();
        });
    }

    log(message, type = 'info') {
        const output = document.getElementById('buildOutput');
        const line = document.createElement('div');
        line.className = `terminal-line ${type}`;
        line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        output.appendChild(line);
        output.scrollTop = output.scrollHeight;
    }

    async handleBuildProject(e) {
        e.preventDefault();

        const formData = new FormData(e.target);
        const features = formData.getAll('features');

        const requestData = {
            project_name: formData.get('projectName'),
            board_type: formData.get('boardType'),
            description: formData.get('description'),
            features: features,
            libraries: this.selectedLibraries,
            materials: this.selectedMaterials,
            board_context: document.getElementById('boardContext').value || null,
            custom_code: document.getElementById('customCode').value || null,
        };

        this.log('Starting project build...', 'info');
        this.log(`Project: ${requestData.project_name}`, 'info');
        this.log(`Board: ${requestData.board_type}`, 'info');

        try {
            const response = await fetch(`${this.apiBase}/build`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData),
            });

            if (!response.ok) {
                throw new Error(`Build failed: ${response.statusText}`);
            }

            const result = await response.json();

            if (result.success) {
                this.log('Project built successfully!', 'success');
                this.log(`Location: ${result.project_path}`, 'info');
                this.log('Files generated:', 'info');

                for (const [filename, _] of Object.entries(result.code_files)) {
                    this.log(`  - ${filename}`, 'info');
                }

                // Clear form and selections
                e.target.reset();
                this.selectedLibraries = [];
                this.selectedMaterials = [];

                // Reload projects list
                this.loadProjects();
            } else {
                this.log(`Build failed: ${result.error}`, 'error');
            }
        } catch (error) {
            this.log(`Error: ${error.message}`, 'error');
        }
    }

    async searchLibraries() {
        const query = document.getElementById('librarySearch').value.trim();
        const boardType = document.getElementById('boardType').value;

        if (!query) {
            this.log('Enter a search query for libraries', 'warning');
            return;
        }

        this.log(`Searching libraries for: ${query}`, 'info');

        try {
            const response = await fetch(`${this.apiBase}/search/libraries`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, board_type: boardType }),
            });

            if (!response.ok) throw new Error('Search failed');

            const results = await response.json();
            this.displayLibraryResults(results);
            this.log(`Found ${results.length} libraries`, 'success');
        } catch (error) {
            this.log(`Library search error: ${error.message}`, 'error');
        }
    }

    displayLibraryResults(results) {
        const container = document.getElementById('libraryResults');

        if (results.length === 0) {
            container.innerHTML = '<div class="empty-state">No libraries found</div>';
            return;
        }

        container.innerHTML = results.map(lib => `
            <div class="result-item" data-library='${JSON.stringify(lib)}'>
                <div class="result-item-header">
                    <span class="result-item-title">${this.escapeHtml(lib.name)}</span>
                    <span class="result-item-meta">${this.escapeHtml(lib.version || '')}</span>
                </div>
                <div class="result-item-description">${this.escapeHtml(lib.description || '')}</div>
            </div>
        `).join('');

        // Add click handlers
        container.querySelectorAll('.result-item').forEach(item => {
            item.addEventListener('click', () => {
                const lib = JSON.parse(item.dataset.library);
                this.selectLibrary(lib);
                item.classList.toggle('selected');
            });
        });
    }

    selectLibrary(lib) {
        const index = this.selectedLibraries.findIndex(l => l.name === lib.name);
        if (index === -1) {
            this.selectedLibraries.push(lib);
            this.log(`Added library: ${lib.name}`, 'success');
        } else {
            this.selectedLibraries.splice(index, 1);
            this.log(`Removed library: ${lib.name}`, 'info');
        }
    }

    async searchMaterials() {
        const query = document.getElementById('materialSearch').value.trim();
        const boardType = document.getElementById('boardType').value;

        if (!query) {
            this.log('Enter a search query for materials', 'warning');
            return;
        }

        this.log(`Searching materials for: ${query}`, 'info');

        try {
            const response = await fetch(`${this.apiBase}/search/materials`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, board_type: boardType }),
            });

            if (!response.ok) throw new Error('Search failed');

            const results = await response.json();
            this.displayMaterialResults(results);
            this.log(`Found ${results.length} components`, 'success');
        } catch (error) {
            this.log(`Material search error: ${error.message}`, 'error');
        }
    }

    displayMaterialResults(results) {
        const container = document.getElementById('materialResults');

        if (results.length === 0) {
            container.innerHTML = '<div class="empty-state">No materials found</div>';
            return;
        }

        container.innerHTML = results.map(mat => `
            <div class="result-item" data-material='${JSON.stringify(mat)}'>
                <div class="result-item-header">
                    <span class="result-item-title">${this.escapeHtml(mat.name)}</span>
                    <span class="result-item-meta">${this.escapeHtml(mat.category || '')}</span>
                </div>
                <div class="result-item-description">${this.escapeHtml(mat.description || '')}</div>
            </div>
        `).join('');

        container.querySelectorAll('.result-item').forEach(item => {
            item.addEventListener('click', () => {
                const mat = JSON.parse(item.dataset.material);
                this.selectMaterial(mat);
                item.classList.toggle('selected');
            });
        });
    }

    selectMaterial(mat) {
        const index = this.selectedMaterials.findIndex(m => m.name === mat.name);
        if (index === -1) {
            this.selectedMaterials.push(mat);
            this.log(`Added component: ${mat.name}`, 'success');
        } else {
            this.selectedMaterials.splice(index, 1);
            this.log(`Removed component: ${mat.name}`, 'info');
        }
    }

    async loadProjects() {
        try {
            const response = await fetch(`${this.apiBase}/projects`);
            if (!response.ok) throw new Error('Failed to load projects');

            const projects = await response.json();
            this.displayProjects(projects);
        } catch (error) {
            this.log(`Failed to load projects: ${error.message}`, 'error');
        }
    }

    displayProjects(projects) {
        const container = document.getElementById('projectsList');

        if (projects.length === 0) {
            container.innerHTML = '<div class="empty-state">No projects yet. Create your first project above.</div>';
            return;
        }

        container.innerHTML = projects.map(project => `
            <div class="project-item" data-project="${this.escapeHtml(project.name)}">
                <span class="project-item-name">${this.escapeHtml(project.name)}</span>
                <div class="project-item-actions">
                    <button class="icon-btn simulate-btn" title="Simulate">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <polygon points="5 3 19 12 5 21 5 3"/>
                        </svg>
                    </button>
                    <button class="icon-btn files-btn" title="View Files">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                            <polyline points="14 2 14 8 20 8"/>
                        </svg>
                    </button>
                </div>
            </div>
        `).join('');

        container.querySelectorAll('.simulate-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const projectName = e.target.closest('.project-item').dataset.project;
                this.simulateProject(projectName);
            });
        });

        container.querySelectorAll('.files-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const projectName = e.target.closest('.project-item').dataset.project;
                this.viewProjectFiles(projectName);
            });
        });
    }

    async simulateProject(projectName) {
        this.log(`Starting simulation for ${projectName}...`, 'info');

        try {
            const response = await fetch(`${this.apiBase}/simulate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ project_name: projectName }),
            });

            if (!response.ok) throw new Error('Simulation failed');

            const result = await response.json();

            this.log(`Simulation started: ${result.project_name}`, 'success');
            this.log(`Board: ${result.board_type}`, 'info');

            if (result.ip_address) {
                this.log(`IP Address: ${result.ip_address}`, 'info');
            }
            if (result.ap_ssid) {
                this.log(`AP SSID: ${result.ap_ssid}`, 'info');
            }
            if (result.web_server) {
                this.log(`Web server running on http://${result.ip_address}`, 'info');
            }

            result.logs.forEach(log => this.log(log, 'info'));
        } catch (error) {
            this.log(`Simulation error: ${error.message}`, 'error');
        }
    }

    async viewProjectFiles(projectName) {
        this.log(`Loading files for ${projectName}...`, 'info');

        try {
            const response = await fetch(`${this.apiBase}/projects/${encodeURIComponent(projectName)}/files`);
            if (!response.ok) throw new Error('Failed to load files');

            const files = await response.json();
            this.log(`Found ${files.length} files:`, 'info');

            files.forEach(file => {
                this.log(`  - ${file.path} (${file.size} bytes)`, 'info');
            });
        } catch (error) {
            this.log(`Error loading files: ${error.message}`, 'error');
        }
    }

    openSettings() {
        document.getElementById('settingsModal').classList.add('active');
    }

    closeSettings() {
        document.getElementById('settingsModal').classList.remove('active');
    }

    saveSettings() {
        const apiKey = document.getElementById('apiKey').value.trim();

        if (apiKey) {
            localStorage.setItem('glm_api_key', apiKey);
            this.log('API key saved to local storage', 'success');
        }

        this.closeSettings();
    }

    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new PoofMicroApp();
});
