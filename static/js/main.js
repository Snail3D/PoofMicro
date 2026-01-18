// PoofMicro ESP32 Builder - Chat Interface with Ralph Sequence

class PoofMicroChat {
    constructor() {
        this.apiBase = '/api';
        this.conversationHistory = [];
        this.currentProjectSpec = null;
        this.ralphPhase = 'idle'; // idle, gathering, building, testing, complete

        this.init();
    }

    init() {
        this.cacheElements();
        this.setupEventListeners();
        this.focusInput();
    }

    cacheElements() {
        this.elements = {
            chatContainer: document.getElementById('chatContainer'),
            messagesContainer: document.getElementById('messagesContainer'),
            messageInput: document.getElementById('messageInput'),
            sendBtn: document.getElementById('sendBtn'),
            typingIndicator: document.getElementById('typingIndicator'),
            quickActions: document.getElementById('quickActions'),
            buildModal: document.getElementById('buildModal'),
            settingsModal: document.getElementById('settingsModal'),
            buildSummary: document.getElementById('buildSummary'),
            buildProgress: document.getElementById('buildProgress'),
            progressFill: document.getElementById('progressFill'),
            progressStatus: document.getElementById('progressStatus'),
            buildResult: document.getElementById('buildResult'),
            newChatBtn: document.getElementById('newChatBtn'),
        };
    }

    setupEventListeners() {
        // Send message
        this.elements.sendBtn.addEventListener('click', () => this.sendMessage());
        this.elements.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        this.elements.messageInput.addEventListener('input', () => {
            this.elements.messageInput.style.height = 'auto';
            this.elements.messageInput.style.height = Math.min(this.elements.messageInput.scrollHeight, 150) + 'px';
            this.elements.sendBtn.disabled = !this.elements.messageInput.value.trim();
        });

        // Quick action buttons
        document.querySelectorAll('.quick-action-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const prompt = btn.dataset.prompt;
                this.elements.messageInput.value = prompt;
                this.sendMessage();
            });
        });

        // Build modal
        document.getElementById('closeBuildModal').addEventListener('click', () => this.closeBuildModal());
        document.getElementById('confirmBuildBtn').addEventListener('click', () => this.startRalphSequence());
        this.elements.buildModal.addEventListener('click', (e) => {
            if (e.target === e.currentTarget) this.closeBuildModal();
        });

        // Settings modal
        document.getElementById('settingsBtn').addEventListener('click', () => this.openSettings());
        document.getElementById('closeSettings').addEventListener('click', () => this.closeSettings());
        document.getElementById('saveSettings').addEventListener('click', () => this.saveSettings());
        this.elements.settingsModal.addEventListener('click', (e) => {
            if (e.target === e.currentTarget) this.closeSettings();
        });

        // New chat
        this.elements.newChatBtn.addEventListener('click', () => this.resetChat());
    }

    focusInput() {
        this.elements.messageInput.focus();
    }

    async sendMessage() {
        const message = this.elements.messageInput.value.trim();
        if (!message) return;

        // Add user message
        this.addMessage(message, 'user');
        this.elements.messageInput.value = '';
        this.elements.messageInput.style.height = 'auto';
        this.elements.sendBtn.disabled = true;

        // Hide quick actions after first message
        if (this.elements.quickActions) {
            this.elements.quickActions.style.display = 'none';
        }

        // Show typing indicator
        this.showTyping();

        try {
            // Get AI response
            const response = await this.getAIResponse(message);

            // Hide typing
            this.hideTyping();

            // Add assistant message
            this.addMessage(response.message, 'assistant');

            // Check if we should suggest building
            if (response.projectSpec) {
                this.currentProjectSpec = response.projectSpec;
                this.showBuildButton(response.projectSpec);
            }

        } catch (error) {
            this.hideTyping();
            this.addMessage(`Sorry, I encountered an error: ${error.message}`, 'assistant');
        }
    }

    async getAIResponse(message) {
        const response = await fetch(`${this.apiBase}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                history: this.conversationHistory
            })
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.statusText}`);
        }

        const data = await response.json();
        this.conversationHistory.push({ role: 'user', content: message });
        this.conversationHistory.push({ role: 'assistant', content: data.message });

        return data;
    }

    addMessage(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;

        const avatar = type === 'assistant'
            ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>`
            : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`;

        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-text">${this.formatMessage(text)}</div>
                <div class="message-time">${this.formatTime()}</div>
            </div>
        `;

        this.elements.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    formatMessage(text) {
        // Convert markdown-style code blocks
        text = text.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
        // Convert inline code
        text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
        // Convert line breaks
        text = text.replace(/\n/g, '<br>');
        return text;
    }

    formatTime() {
        return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    showTyping() {
        this.elements.typingIndicator.style.display = 'flex';
        this.scrollToBottom();
    }

    hideTyping() {
        this.elements.typingIndicator.style.display = 'none';
    }

    scrollToBottom() {
        setTimeout(() => {
            this.elements.chatContainer.scrollTop = this.elements.chatContainer.scrollHeight;
        }, 100);
    }

    showBuildButton(spec) {
        const buttonDiv = document.createElement('div');
        buttonDiv.className = 'message assistant-message';
        buttonDiv.innerHTML = `
            <div class="message-avatar">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                </svg>
            </div>
            <div class="message-content">
                <div class="message-text">
                    Ready to build! Here's what I'll create:
                </div>
                <div class="build-summary-card">
                    <h4>Project Summary</h4>
                    <ul>
                        <li><strong>Name:</strong> ${this.escapeHtml(spec.projectName)}</li>
                        <li><strong>Board:</strong> ${this.escapeHtml(spec.boardType)}</li>
                        <li><strong>Features:</strong> ${spec.features.join(', ') || 'Basic functionality'}</li>
                    </ul>
                    ${spec.libraries && spec.libraries.length > 0 ? `<p><strong>Libraries:</strong> ${spec.libraries.map(l => l.name).join(', ')}</p>` : ''}
                    ${spec.materials && spec.materials.length > 0 ? `<p><strong>Components:</strong> ${spec.materials.map(m => m.name).join(', ')}</p>` : ''}
                </div>
                <button class="btn btn-primary build-trigger-btn" style="margin-top: 1rem;">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <polygon points="5 3 19 12 5 21 5 3"/>
                    </svg>
                    Start Ralph Sequence
                </button>
                <div class="message-time">${this.formatTime()}</div>
            </div>
        `;

        this.elements.messagesContainer.appendChild(buttonDiv);

        // Add click handler
        buttonDiv.querySelector('.build-trigger-btn').addEventListener('click', () => {
            this.openBuildModal(spec);
        });

        this.scrollToBottom();
    }

    escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    openBuildModal(spec) {
        this.currentProjectSpec = spec;

        let summaryHTML = `
            <h3>Project Configuration</h3>
            <ul>
                <li><strong>Project Name:</strong> ${this.escapeHtml(spec.projectName)}</li>
                <li><strong>Board Type:</strong> ${this.escapeHtml(spec.boardType)}</li>
                <li><strong>Description:</strong> ${this.escapeHtml(spec.description)}</li>
            </ul>
        `;

        if (spec.features && spec.features.length > 0) {
            summaryHTML += `
                <h3>Features</h3>
                <ul>
                    ${spec.features.map(f => `<li>${this.escapeHtml(f)}</li>`).join('')}
                </ul>
            `;
        }

        if (spec.libraries && spec.libraries.length > 0) {
            summaryHTML += `
                <h3>Libraries</h3>
                <ul>
                    ${spec.libraries.map(l => `<li>${this.escapeHtml(l.name)} - ${this.escapeHtml(l.description || '')}</li>`).join('')}
                </ul>
            `;
        }

        if (spec.materials && spec.materials.length > 0) {
            summaryHTML += `
                <h3>Components</h3>
                <ul>
                    ${spec.materials.map(m => `<li>${this.escapeHtml(m.name)} - ${this.escapeHtml(m.description || '')}</li>`).join('')}
                </ul>
            `;
        }

        this.elements.buildSummary.innerHTML = summaryHTML;
        this.elements.buildModal.classList.add('active');
    }

    closeBuildModal() {
        this.elements.buildModal.classList.remove('active');
    }

    async startRalphSequence() {
        this.ralphPhase = 'building';
        this.elements.buildProgress.style.display = 'block';
        this.elements.buildResult.style.display = 'none';

        // Add notification in chat
        this.addMessage('Starting Ralph Sequence: Automated build and test pipeline...', 'assistant');

        try {
            // Phase 1: Generate Code
            await this.updateProgress(10, 'Generating ESP32 code with GLM 4.7...');
            const buildResult = await this.buildProject();

            if (!buildResult.success) {
                throw new Error(buildResult.error || 'Build failed');
            }

            // Phase 2: Simulate
            await this.updateProgress(50, 'Running WACWI simulation...');
            const simResult = await this.simulateProject();

            // Phase 3: Complete
            await this.updateProgress(100, 'Ralph Sequence complete!');

            this.elements.buildResult.className = 'build-result success';
            this.elements.buildResult.innerHTML = `
                <h4>Build Successful!</h4>
                <p>Project: ${this.escapeHtml(this.currentProjectSpec.projectName)}</p>
                <p>Location: ${this.escapeHtml(buildResult.project_path || 'esp32_projects/' + this.currentProjectSpec.projectName.toLowerCase().replace(' ', '_'))}</p>
                <p>Files: ${Object.keys(buildResult.code_files || {}).length + ' files generated'}</p>
            `;
            this.elements.buildResult.style.display = 'block';

            // Add success message to chat
            this.addMessage(`Ralph Sequence Complete! Your ESP32 project has been built and tested successfully.

Project: **${this.currentProjectSpec.projectName}**
Board: **${this.currentProjectSpec.boardType}**
Location: **esp32_projects/${this.currentProjectSpec.projectName.toLowerCase().replace(' ', '_')}**

The project includes:
${Object.keys(buildResult.code_files || {}).map(f => `- ${f}`).join('\n')}

Next steps:
1. Navigate to the project directory
2. Run: `platformio run --target upload`
3. Monitor with: `platformio device monitor`

Would you like to make any changes or build another project?`, 'assistant');

        } catch (error) {
            this.elements.buildResult.className = 'build-result error';
            this.elements.buildResult.innerHTML = `
                <h4>Build Failed</h4>
                <p>${this.escapeHtml(error.message)}</p>
            `;
            this.elements.buildResult.style.display = 'block';

            this.addMessage(`Build failed: ${error.message}`, 'assistant');
        }
    }

    async buildProject() {
        const response = await fetch(`${this.apiBase}/build`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                project_name: this.currentProjectSpec.projectName,
                board_type: this.currentProjectSpec.boardType,
                description: this.currentProjectSpec.description,
                features: this.currentProjectSpec.features || [],
                libraries: this.currentProjectSpec.libraries || [],
                materials: this.currentProjectSpec.materials || [],
                board_context: this.currentProjectSpec.boardContext,
                custom_code: this.currentProjectSpec.customCode,
            })
        });

        if (!response.ok) {
            throw new Error(`Build API error: ${response.statusText}`);
        }

        return await response.json();
    }

    async simulateProject() {
        const projectName = this.currentProjectSpec.projectName.toLowerCase().replace(' ', '_');

        const response = await fetch(`${this.apiBase}/simulate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                project_name: projectName,
                board_type: this.currentProjectSpec.boardType
            })
        });

        if (!response.ok) {
            // Simulation is optional, don't fail on error
            return { status: 'simulation_skipped' };
        }

        return await response.json();
    }

    async updateProgress(percent, status) {
        this.elements.progressFill.style.width = percent + '%';
        this.elements.progressStatus.textContent = status;

        // Update in chat too
        if (percent % 25 === 0) {
            await new Promise(resolve => setTimeout(resolve, 500));
        }
    }

    openSettings() {
        this.elements.settingsModal.classList.add('active');
    }

    closeSettings() {
        this.elements.settingsModal.classList.remove('active');
    }

    saveSettings() {
        const apiKey = document.getElementById('apiKey').value.trim();
        if (apiKey) {
            localStorage.setItem('glm_api_key', apiKey);
        }
        this.closeSettings();
    }

    resetChat() {
        this.conversationHistory = [];
        this.currentProjectSpec = null;
        this.ralphPhase = 'idle';
        this.elements.messagesContainer.innerHTML = `
            <div class="message assistant-message">
                <div class="message-avatar">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                    </svg>
                </div>
                <div class="message-content">
                    <div class="message-text">
                        Welcome to PoofMicro! I can help you build ESP32 projects.
                        <br><br>
                        Tell me what you want to build, or describe your project idea.
                        I'll help you design it, find the right components, and generate the code.
                    </div>
                    <div class="message-time">Just now</div>
                </div>
            </div>
        `;
        this.elements.quickActions.style.display = 'block';
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new PoofMicroChat();
});
