// Interview Page JavaScript
class InterviewManager {
    constructor() {
        this.currentInterview = null;
        this.currentAgentId = null;
        this.currentTranscript = null;
        this.interviewHistory = [];
        this.selectedInterviews = new Set();
        this.apiBaseUrl = ''; // Use relative URLs to Flask app
        this.init();
    }

    init() {
        this.bindEventListeners();
        this.hideLoading();
        this.loadInterviewHistory();
    }

    bindEventListeners() {
        // Form submission
        document.getElementById('interview-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createInterview();
        });

        // Control buttons
        document.getElementById('refresh-interview-btn').addEventListener('click', () => {
            this.refreshInterview();
        });

        document.getElementById('get-transcript-btn').addEventListener('click', () => {
            this.getTranscript();
        });

        document.getElementById('new-interview-btn').addEventListener('click', () => {
            this.startNewInterview();
        });

        document.getElementById('download-transcript-btn').addEventListener('click', () => {
            this.downloadTranscript();
        });

        document.getElementById('analyze-transcript-btn').addEventListener('click', () => {
            this.analyzeTranscript();
        });

        // History controls
        document.getElementById('refresh-history-btn').addEventListener('click', () => {
            this.loadInterviewHistory();
        });

        document.getElementById('select-all-btn').addEventListener('click', () => {
            this.selectAllInterviews();
        });

        document.getElementById('clear-selection-btn').addEventListener('click', () => {
            this.clearSelection();
        });

        document.getElementById('analyze-selected-btn').addEventListener('click', () => {
            this.analyzeSelectedCandidates();
        });

        // Search and filter
        document.getElementById('search-candidates').addEventListener('input', (e) => {
            this.filterHistory();
        });

        document.getElementById('status-filter').addEventListener('change', (e) => {
            this.filterHistory();
        });

        // Error modal close
        document.getElementById('error-modal-close').addEventListener('click', () => {
            this.hideErrorModal();
        });
    }

    async loadInterviewHistory() {
        this.showLoading('Loading interview history...');
        
        try {
            const response = await fetch('/api/interview-history');
            
            if (response.ok) {
                const data = await response.json();
                this.interviewHistory = data.interviews || [];
                this.renderInterviewHistory();
            } else {
                // If endpoint doesn't exist yet, show sample data
                this.interviewHistory = this.generateSampleHistory();
                this.renderInterviewHistory();
            }
        } catch (error) {
            console.error('Error loading interview history:', error);
            // Show sample data on error
            this.interviewHistory = this.generateSampleHistory();
            this.renderInterviewHistory();
        } finally {
            this.hideLoading();
        }
    }

    generateSampleHistory() {
        // Sample data for demonstration
        return [
            {
                agent_id: 'agent_001',
                candidate_name: 'John Smith',
                role: 'Software Engineer',
                status: 'completed',
                created_at: '2024-01-15T10:30:00Z',
                duration: '25 minutes',
                has_transcript: true
            },
            {
                agent_id: 'agent_002',
                candidate_name: 'Sarah Johnson',
                role: 'Frontend Developer',
                status: 'completed',
                created_at: '2024-01-14T14:15:00Z',
                duration: '30 minutes',
                has_transcript: true
            },
            {
                agent_id: 'agent_003',
                candidate_name: 'Mike Davis',
                role: 'Backend Developer',
                status: 'in-progress',
                created_at: '2024-01-16T09:00:00Z',
                duration: 'In progress',
                has_transcript: false
            }
        ];
    }

    renderInterviewHistory() {
        const historyGrid = document.getElementById('history-grid');
        const historyEmpty = document.getElementById('history-empty');
        
        if (this.interviewHistory.length === 0) {
            historyGrid.style.display = 'none';
            historyEmpty.style.display = 'block';
            return;
        }
        
        historyGrid.style.display = 'grid';
        historyEmpty.style.display = 'none';
        
        historyGrid.innerHTML = this.interviewHistory.map(interview => `
            <div class="history-item" data-agent-id="${interview.agent_id}">
                <div class="history-item-header">
                    <div class="history-checkbox ${this.selectedInterviews.has(interview.agent_id) ? 'checked' : ''}" 
                         data-agent-id="${interview.agent_id}">
                        ${this.selectedInterviews.has(interview.agent_id) ? '<i class="fas fa-check"></i>' : ''}
                    </div>
                    <div class="history-status ${interview.status}">
                        <i class="fas fa-circle"></i>
                        ${interview.status}
                    </div>
                </div>
                
                <div class="history-info">
                    <h4>${interview.candidate_name}</h4>
                    <div class="role">${interview.role}</div>
                    ${interview.email ? `<div class="email">${interview.email}</div>` : ''}
                </div>
                
                <div class="history-meta">
                    <div class="history-date">
                        <i class="fas fa-calendar"></i>
                        ${new Date(interview.created_at).toLocaleDateString()}
                    </div>
                    <div class="history-actions-item">
                        ${interview.has_transcript ? 
                            `<button class="btn btn-secondary view-transcript-btn" data-agent-id="${interview.agent_id}">
                                <i class="fas fa-file-alt"></i> View
                            </button>` : ''
                        }
                        <button class="btn btn-primary resume-interview-btn" data-agent-id="${interview.agent_id}" 
                                data-name="${interview.candidate_name}" data-role="${interview.role}">
                            <i class="fas fa-play"></i> Resume
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
        
        // Bind checkbox events
        document.querySelectorAll('.history-checkbox').forEach(checkbox => {
            checkbox.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleInterviewSelection(checkbox.dataset.agentId);
            });
        });
        
        // Bind view transcript events
        document.querySelectorAll('.view-transcript-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.viewHistoryTranscript(btn.dataset.agentId);
            });
        });
        
        // Bind resume interview events
        document.querySelectorAll('.resume-interview-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.resumeInterview(btn.dataset.agentId, btn.dataset.name, btn.dataset.role);
            });
        });
        
        this.updateSelectionCounter();
    }

    toggleInterviewSelection(agentId) {
        if (this.selectedInterviews.has(agentId)) {
            this.selectedInterviews.delete(agentId);
        } else {
            this.selectedInterviews.add(agentId);
        }
        
        // Update UI
        const checkbox = document.querySelector(`[data-agent-id="${agentId}"].history-checkbox`);
        const historyItem = document.querySelector(`[data-agent-id="${agentId}"].history-item`);
        
        if (this.selectedInterviews.has(agentId)) {
            checkbox.classList.add('checked');
            checkbox.innerHTML = '<i class="fas fa-check"></i>';
            historyItem.classList.add('selected');
        } else {
            checkbox.classList.remove('checked');
            checkbox.innerHTML = '';
            historyItem.classList.remove('selected');
        }
        
        this.updateSelectionCounter();
    }

    selectAllInterviews() {
        const visibleInterviews = document.querySelectorAll('.history-item:not([style*="display: none"])');
        
        visibleInterviews.forEach(item => {
            const agentId = item.dataset.agentId;
            if (!this.selectedInterviews.has(agentId)) {
                this.selectedInterviews.add(agentId);
                
                const checkbox = item.querySelector('.history-checkbox');
                checkbox.classList.add('checked');
                checkbox.innerHTML = '<i class="fas fa-check"></i>';
                item.classList.add('selected');
            }
        });
        
        this.updateSelectionCounter();
    }

    clearSelection() {
        this.selectedInterviews.clear();
        
        document.querySelectorAll('.history-checkbox').forEach(checkbox => {
            checkbox.classList.remove('checked');
            checkbox.innerHTML = '';
        });
        
        document.querySelectorAll('.history-item').forEach(item => {
            item.classList.remove('selected');
        });
        
        this.updateSelectionCounter();
    }

    updateSelectionCounter() {
        const count = this.selectedInterviews.size;
        document.getElementById('selected-count').textContent = count;
        document.getElementById('analyze-selected-btn').disabled = count === 0;
    }

    filterHistory() {
        const searchTerm = document.getElementById('search-candidates').value.toLowerCase();
        const statusFilter = document.getElementById('status-filter').value;
        
        document.querySelectorAll('.history-item').forEach(item => {
            const candidateName = item.querySelector('.history-info h4').textContent.toLowerCase();
            const role = item.querySelector('.role').textContent.toLowerCase();
            const status = item.querySelector('.history-status').textContent.trim().toLowerCase();
            
            const matchesSearch = candidateName.includes(searchTerm) || role.includes(searchTerm);
            const matchesStatus = statusFilter === 'all' || status === statusFilter;
            
            if (matchesSearch && matchesStatus) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    }

    async viewHistoryTranscript(agentId) {
        const interview = this.interviewHistory.find(i => i.agent_id === agentId);
        if (!interview) return;
        
        this.showLoading('Loading transcript...');
        
        try {
            const response = await fetch(
                `/api/interview-transcript/${agentId}?candidate_name=${encodeURIComponent(interview.candidate_name)}&role=${encodeURIComponent(interview.role)}`
            );

            if (response.ok) {
                const transcriptData = await response.json();
                this.showTranscript(transcriptData);
            } else {
                this.showError('Failed to load transcript');
            }
        } catch (error) {
            this.showError(`Error loading transcript: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    resumeInterview(agentId, candidateName, role) {
        // Set up the interview session with existing data
        this.currentAgentId = agentId;
        this.currentInterview = {
            agent_id: agentId,
            candidate_name: candidateName,
            role: role,
            interview_link: `https://agent.ai-interviewer.com/${agentId}` // Construct the link
        };
        
        this.showInterviewSession(this.currentInterview);
    }

    async analyzeSelectedCandidates() {
        if (this.selectedInterviews.size === 0) {
            this.showError('Please select at least one candidate for analysis.');
            return;
        }
        
        this.showLoading('Analyzing selected candidates...');
        
        try {
            const selectedCandidates = Array.from(this.selectedInterviews).map(agentId => {
                const interview = this.interviewHistory.find(i => i.agent_id === agentId);
                return {
                    agent_id: agentId,
                    candidate_name: interview.candidate_name,
                    role: interview.role
                };
            });
            
            // For now, redirect to dashboard with analysis parameters
            const analysisParams = new URLSearchParams();
            analysisParams.set('analyze_interviews', JSON.stringify(selectedCandidates));
            
            window.location.href = `/dashboard?${analysisParams.toString()}`;
            
        } catch (error) {
            console.error('Error analyzing candidates:', error);
            this.showError(`Failed to analyze candidates: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    async createInterview() {
        const form = document.getElementById('interview-form');
        const formData = new FormData(form);
        
        const data = {
            candidate_name: formData.get('candidate_name'),
            role: formData.get('role'),
            candidate_email: formData.get('candidate_email') || null
        };

        // Validate required fields
        if (!data.candidate_name || !data.role) {
            this.showError('Please fill in all required fields.');
            return;
        }

        this.showLoading('Creating interview session...');

        try {
            const response = await fetch(`/api/create-interview`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            this.currentInterview = result;
            this.currentAgentId = result.agent_id;
            
            this.showInterviewSession(result);
            
        } catch (error) {
            console.error('Error creating interview:', error);
            this.showError(`Failed to create interview: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    showInterviewSession(interviewData) {
        // Hide setup section
        document.getElementById('interview-setup').style.display = 'none';
        
        // Show interview session
        const sessionSection = document.getElementById('interview-session');
        sessionSection.style.display = 'block';

        // Update candidate info
        const candidateInfo = document.getElementById('current-candidate-info');
        candidateInfo.textContent = `${interviewData.candidate_name} - ${interviewData.role}`;

        // Set iframe source
        const iframe = document.getElementById('interview-iframe');
        iframe.src = interviewData.interview_link;

        // Update status
        this.updateInterviewStatus('Live', 'success');

        // Scroll to interview section
        sessionSection.scrollIntoView({ behavior: 'smooth' });
    }

    refreshInterview() {
        if (this.currentInterview) {
            const iframe = document.getElementById('interview-iframe');
            iframe.src = iframe.src; // Refresh the iframe
            this.updateInterviewStatus('Refreshed', 'success');
        }
    }

    async getTranscript() {
        if (!this.currentAgentId) {
            this.showError('No active interview session found.');
            return;
        }

        this.showLoading('Retrieving transcript...');
        
        try {
            const candidateName = this.currentInterview.candidate_name;
            const role = this.currentInterview.role;
            
            const response = await fetch(
                `/api/interview-transcript/${this.currentAgentId}?candidate_name=${encodeURIComponent(candidateName)}&role=${encodeURIComponent(role)}`
            );

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || errorData.detail || `HTTP error! status: ${response.status}`);
            }

            const transcriptData = await response.json();
            
            if (!transcriptData.success) {
                throw new Error(transcriptData.error || 'Failed to retrieve transcript');
            }

            this.showTranscript(transcriptData);
            
        } catch (error) {
            console.error('Error getting transcript:', error);
            this.showError(`Failed to get transcript: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    showTranscript(transcriptData) {
        const transcriptSection = document.getElementById('transcript-section');
        const transcriptContent = document.getElementById('transcript-content');
        
        // Store transcript data for download
        this.currentTranscript = transcriptData;

        if (transcriptData.messages && transcriptData.messages.length > 0) {
            const messagesHtml = transcriptData.messages.map(message => `
                <div class="transcript-message">
                    <div class="transcript-speaker">${message.role === 'user' ? 'Candidate' : 'AI Interviewer'}</div>
                    <div class="transcript-text">${message.content}</div>
                    <div class="transcript-timestamp">${new Date(message.timestamp || Date.now()).toLocaleString()}</div>
                </div>
            `).join('');
            
            transcriptContent.innerHTML = messagesHtml;
        } else if (transcriptData.formatted_transcript) {
            transcriptContent.innerHTML = `
                <div class="transcript-message">
                    <div class="transcript-speaker">Interview Transcript</div>
                    <div class="transcript-text">${JSON.stringify(transcriptData.formatted_transcript, null, 2)}</div>
                </div>
            `;
        } else {
            transcriptContent.innerHTML = `
                <div class="transcript-message">
                    <div class="transcript-speaker">System</div>
                    <div class="transcript-text">No transcript content available yet. The interview may still be in progress.</div>
                </div>
            `;
        }

        transcriptSection.style.display = 'block';
        transcriptSection.scrollIntoView({ behavior: 'smooth' });
    }

    downloadTranscript() {
        if (!this.currentTranscript) {
            this.showError('No transcript available to download.');
            return;
        }

        const filename = `interview_transcript_${this.currentInterview.candidate_name.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.json`;
        const data = JSON.stringify(this.currentTranscript, null, 2);
        
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    analyzeTranscript() {
        if (!this.currentTranscript) {
            this.showError('No transcript available to analyze.');
            return;
        }

        // Redirect to dashboard with analysis
        const candidateName = this.currentInterview.candidate_name;
        const role = this.currentInterview.role;
        
        // Redirect to dashboard with analysis
        window.location.href = `/dashboard?analyze=${encodeURIComponent(candidateName)}&role=${encodeURIComponent(role)}`;
    }

    startNewInterview() {
        // Reset state
        this.currentInterview = null;
        this.currentAgentId = null;
        this.currentTranscript = null;

        // Reset form
        document.getElementById('interview-form').reset();

        // Show setup section
        document.getElementById('interview-setup').style.display = 'block';
        document.getElementById('interview-session').style.display = 'none';
        document.getElementById('transcript-section').style.display = 'none';

        // Clear iframe
        document.getElementById('interview-iframe').src = '';

        // Scroll to top
        document.getElementById('interview-setup').scrollIntoView({ behavior: 'smooth' });
    }

    updateInterviewStatus(status, type = 'info') {
        const statusElement = document.getElementById('interview-status');
        if (!statusElement) {
            console.warn('Interview status element not found');
            return;
        }
        
        const indicator = statusElement.querySelector('.status-indicator');
        console.log("interview status: " + status);
        
        // Try different selectors to find the status text element
        let statusTextElement = statusElement.querySelector('i + *');
        if (!statusTextElement) {
            // Try alternative selectors
            statusTextElement = statusElement.querySelector('.status-text');
            if (!statusTextElement) {
                statusTextElement = statusElement.querySelector('span');
                if (!statusTextElement) {
                    // Create a status text element if none exists
                    statusTextElement = document.createElement('span');
                    statusTextElement.className = 'status-text';
                    statusElement.appendChild(statusTextElement);
                }
            }
        }
        
        if (statusTextElement) {
            statusTextElement.textContent = status;
        }
        
        // Update status color
        statusElement.className = 'interview-status';
        statusElement.classList.add(`status-${type}`);
        
        // Add corresponding CSS if needed
        const colors = {
            success: '#10b981',
            warning: '#f59e0b',
            error: '#ef4444',
            info: '#3b82f6'
        };
        
        if (colors[type]) {
            statusElement.style.background = `${colors[type]}20`;
            statusElement.style.color = colors[type];
            if (indicator) {
                indicator.style.color = colors[type];
            }
        }
    }

    showLoading(message = 'Loading...') {
        const loadingOverlay = document.getElementById('loading-overlay');
        const loadingMessage = document.getElementById('loading-message');
        
        loadingMessage.textContent = message;
        loadingOverlay.style.display = 'flex';
    }

    hideLoading() {
        const loadingOverlay = document.getElementById('loading-overlay');
        loadingOverlay.style.display = 'none';
    }

    showError(message) {
        const errorModal = document.getElementById('error-modal');
        const errorMessage = document.getElementById('error-message');
        
        errorMessage.textContent = message;
        errorModal.style.display = 'flex';
    }

    hideErrorModal() {
        const errorModal = document.getElementById('error-modal');
        errorModal.style.display = 'none';
    }
}

// Initialize the interview manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new InterviewManager();
}); 