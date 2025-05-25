// Dashboard JavaScript - Interactive Functionality
class TeamCompatibilityDashboard {
    constructor() {
        this.data = null;
        this.charts = {};
        this.filteredCandidates = [];
        this.init();
    }

    async init() {
        try {
            // Check for analysis parameters from interview page
            this.checkForInterviewAnalysis();
            
            await this.loadData();
            this.hideLoading();
            this.populateOverview();
            this.renderCharts();
            this.renderTeamMembers();
            this.renderCandidates();
            this.initEventListeners();
        } catch (error) {
            console.error('Dashboard initialization failed:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    checkForInterviewAnalysis() {
        const urlParams = new URLSearchParams(window.location.search);
        const analyzeInterviews = urlParams.get('analyze_interviews');
        
        if (analyzeInterviews) {
            try {
                const candidatesData = JSON.parse(analyzeInterviews);
                this.handleInterviewAnalysis(candidatesData);
            } catch (error) {
                console.error('Error parsing interview analysis data:', error);
            }
        }
    }

    async handleInterviewAnalysis(candidatesData) {
        // Show notification for interview analysis
        this.showAnalysisNotification(candidatesData);
        
        // Here you could trigger actual analysis
        // For now, we'll just highlight that these candidates were selected for analysis
        console.log('Interview candidates selected for analysis:', candidatesData);
        
        // Store the interview candidates for highlighting
        this.interviewCandidates = candidatesData;
        
        // Clean URL after processing
        window.history.replaceState({}, document.title, window.location.pathname);
    }

    showAnalysisNotification(candidatesData) {
        const notification = document.createElement('div');
        notification.className = 'analysis-notification';
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-header">
                    <i class="fas fa-brain"></i>
                    <h4>Interview Analysis</h4>
                    <button class="notification-close" onclick="this.parentElement.parentElement.parentElement.remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <p>Analyzing ${candidatesData.length} candidate${candidatesData.length > 1 ? 's' : ''} from interview data:</p>
                <ul class="candidates-list">
                    ${candidatesData.map(c => `<li><strong>${c.candidate_name}</strong> - ${c.role}</li>`).join('')}
                </ul>
                <div class="notification-actions">
                    <button class="btn btn-primary" onclick="this.parentElement.parentElement.parentElement.remove()">
                        <i class="fas fa-check"></i> Continue Analysis
                    </button>
                </div>
            </div>
        `;
        
        // Add notification styles
        const style = document.createElement('style');
        style.textContent = `
            .analysis-notification {
                position: fixed;
                top: 20px;
                right: 20px;
                background: white;
                border-radius: 8px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.15);
                border-left: 4px solid var(--primary-color);
                max-width: 400px;
                z-index: 1000;
                animation: slideInRight 0.3s ease;
            }
            
            .notification-content {
                padding: 1.5rem;
            }
            
            .notification-header {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin-bottom: 1rem;
            }
            
            .notification-header h4 {
                margin: 0;
                flex: 1;
                color: var(--primary-color);
            }
            
            .notification-close {
                background: none;
                border: none;
                color: var(--text-secondary);
                cursor: pointer;
                padding: 0.25rem;
                border-radius: 4px;
            }
            
            .notification-close:hover {
                background: var(--secondary-color);
            }
            
            .candidates-list {
                margin: 0.75rem 0;
                padding-left: 1.25rem;
            }
            
            .candidates-list li {
                margin-bottom: 0.25rem;
                font-size: 0.9rem;
            }
            
            .notification-actions {
                margin-top: 1rem;
                display: flex;
                justify-content: flex-end;
            }
            
            @keyframes slideInRight {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        
        document.head.appendChild(style);
        document.body.appendChild(notification);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 10000);
    }

    async loadData() {
        try {
            const response = await fetch('/api/dashboard-data');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            this.data = await response.json();
            this.filteredCandidates = [...this.data.candidates_analysis];
            
            // Debug log for compatibility data
            console.log('🔍 Debug - Team Insights:', this.data.team_insights);
            console.log('🔍 Debug - Pool Summary:', this.data.team_insights?.candidate_pool_summary);
            
        } catch (error) {
            console.error('Error loading data:', error);
            throw error;
        }
    }

    hideLoading() {
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
        }
    }

    showError(message) {
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.innerHTML = `
                <div class="loading-spinner">
                    <i class="fas fa-exclamation-triangle" style="color: var(--danger-color);"></i>
                    <p>${message}</p>
                </div>
            `;
        }
    }

    populateOverview() {
        try {
            const metadata = this.data.analysis_metadata;
            const insights = this.data.team_insights;

            // Update overview cards with better error handling
            const teamSizeElement = document.getElementById('team-size');
            const candidatesCountElement = document.getElementById('candidates-count');
            const avgCompatibilityElement = document.getElementById('avg-compatibility');
            const topCandidatesElement = document.getElementById('top-candidates-count');

            if (teamSizeElement) teamSizeElement.textContent = metadata?.team_size || 'N/A';
            if (candidatesCountElement) candidatesCountElement.textContent = metadata?.candidates_count || 'N/A';
            
            // Enhanced compatibility display with debugging
            if (avgCompatibilityElement && insights?.candidate_pool_summary?.average_compatibility !== undefined) {
                const rawCompatibility = insights.candidate_pool_summary.average_compatibility;
                const formattedCompatibility = (rawCompatibility * 100).toFixed(1) + '%';
                avgCompatibilityElement.textContent = formattedCompatibility;
                
                console.log('✅ Compatibility Display:', {
                    raw: rawCompatibility,
                    formatted: formattedCompatibility,
                    element: avgCompatibilityElement
                });
            } else {
                if (avgCompatibilityElement) avgCompatibilityElement.textContent = 'N/A';
                console.warn('⚠️ Compatibility data missing or element not found');
            }
            
            if (topCandidatesElement) {
                topCandidatesElement.textContent = insights?.candidate_pool_summary?.candidates_above_threshold || 'N/A';
            }

            // Update analysis time
            const analysisTimeElement = document.getElementById('analysis-time');
            if (analysisTimeElement && metadata?.timestamp) {
                const analysisTime = new Date(metadata.timestamp).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
                analysisTimeElement.textContent = analysisTime;
            }
        } catch (error) {
            console.error('Error populating overview:', error);
        }
    }

    renderCharts() {
        this.renderCompatibilityChart();
        this.renderRecommendationChart();
    }

    renderCompatibilityChart() {
        const ctx = document.getElementById('compatibilityChart');
        if (!ctx) return;

        const candidates = this.data.candidates_analysis;
        const labels = candidates.map(c => c.candidate_info.name);
        const scores = candidates.map(c => c.ai_analysis.compatibility_score * 100);
        
        // Color coding based on recommendation
        const colors = candidates.map(c => {
            const recommendation = c.overall_recommendation.status;
            switch (recommendation) {
                case 'HIGHLY RECOMMENDED': return '#10b981';
                case 'RECOMMENDED': return '#3b82f6';
                case 'CONDITIONALLY RECOMMENDED': return '#f59e0b';
                case 'NOT RECOMMENDED': return '#ef4444';
                default: return '#6b7280';
            }
        });

        this.charts.compatibility = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Compatibility Score (%)',
                    data: scores,
                    backgroundColor: colors,
                    borderColor: colors,
                    borderWidth: 1,
                    borderRadius: 4,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                // Disable animations to prevent resizing issues
                animation: {
                    duration: 0
                },
                transitions: {
                    active: {
                        animation: {
                            duration: 0
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Compatibility: ${context.parsed.y.toFixed(1)}%`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    },
                    x: {
                        ticks: {
                            maxRotation: 45,
                            minRotation: 0
                        }
                    }
                },
                // Prevent resize loops
                onResize: function(chart, size) {
                    // Limit resize frequency
                    clearTimeout(chart.resizeTimeout);
                    chart.resizeTimeout = setTimeout(() => {
                        chart.update('none');
                    }, 100);
                }
            }
        });
    }

    renderRecommendationChart() {
        const ctx = document.getElementById('recommendationChart');
        if (!ctx) return;

        const recommendations = {};
        this.data.candidates_analysis.forEach(candidate => {
            const status = candidate.overall_recommendation.status;
            recommendations[status] = (recommendations[status] || 0) + 1;
        });

        const labels = Object.keys(recommendations);
        const data = Object.values(recommendations);
        const colors = labels.map(label => {
            switch (label) {
                case 'HIGHLY RECOMMENDED': return '#10b981';
                case 'RECOMMENDED': return '#3b82f6';
                case 'CONDITIONALLY RECOMMENDED': return '#f59e0b';
                case 'NOT RECOMMENDED': return '#ef4444';
                default: return '#6b7280';
            }
        });

        this.charts.recommendation = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels.map(label => this.formatRecommendationLabel(label)),
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderColor: '#ffffff',
                    borderWidth: 3,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                // Disable animations to prevent resizing issues
                animation: {
                    duration: 0
                },
                transitions: {
                    active: {
                        animation: {
                            duration: 0
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${context.parsed} (${percentage}%)`;
                            }
                        }
                    }
                },
                // Prevent resize loops
                onResize: function(chart, size) {
                    clearTimeout(chart.resizeTimeout);
                    chart.resizeTimeout = setTimeout(() => {
                        chart.update('none');
                    }, 100);
                }
            }
        });
    }

    formatRecommendationLabel(label) {
        return label.split(' ').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
        ).join(' ');
    }

    renderTeamMembers() {
        const container = document.getElementById('team-members');
        if (!container) return;

        const members = this.data.team_summary.members;
        container.innerHTML = members.map(member => `
            <div class="team-member">
                <div class="member-header">
                    <div class="member-avatar">
                        ${this.getInitials(member.name)}
                    </div>
                    <div class="member-info">
                        <h4>${member.name}</h4>
                        <p>${member.position}</p>
                    </div>
                </div>
                <div class="member-traits">
                    ${Object.entries(member.traits_summary).map(([trait, value]) => `
                        <div class="trait-item">
                            <span>${this.formatTraitName(trait)}</span>
                            <span class="trait-value">${(value * 100).toFixed(0)}%</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('');
    }

    renderCandidates() {
        const container = document.getElementById('candidates-grid');
        if (!container) return;

        // Clean up existing radar charts
        this.cleanupRadarCharts();

        container.innerHTML = this.filteredCandidates.map(candidate => {
            const info = candidate.candidate_info;
            const aiAnalysis = candidate.ai_analysis;
            const recommendation = candidate.overall_recommendation;

            const compatibilityPercentage = (aiAnalysis.compatibility_score * 100).toFixed(1);
            const recommendationClass = this.getRecommendationClass(recommendation.status);

            return `
                <div class="candidate-card ${recommendationClass}" data-candidate-id="${info.id}">
                    <div class="candidate-header">
                        <div class="candidate-info">
                            <h4>${info.name}</h4>
                            <p>${info.position}</p>
                        </div>
                        <div class="compatibility-score">
                            <div class="score-value" style="color: ${this.getScoreColor(aiAnalysis.compatibility_score)}">${compatibilityPercentage}%</div>
                            <div class="score-label">Compatibility</div>
                        </div>
                    </div>
                    <div class="recommendation-badge ${recommendationClass}">
                        ${this.formatRecommendationLabel(recommendation.status)}
                    </div>
                    <div class="candidate-content">
                        <div class="radar-chart-container">
                            <canvas id="radarChart-${info.id}" class="radar-chart" width="140" height="140"></canvas>
                        </div>
                        <div class="candidate-highlights">
                            <h5>Key Strengths</h5>
                            <ul class="highlights-list">
                                ${aiAnalysis.strengths.slice(0, 2).map(strength => 
                                    `<li>${strength}</li>`
                                ).join('')}
                            </ul>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        // Add click handlers for candidate cards and create radar charts
        container.querySelectorAll('.candidate-card').forEach(card => {
            card.addEventListener('click', () => {
                const candidateId = card.dataset.candidateId;
                this.showCandidateDetails(candidateId);
            });
        });

        // Create radar charts for each candidate
        this.filteredCandidates.forEach(candidate => {
            this.createRadarChart(candidate);
        });
    }

    getInitials(name) {
        return name.split(' ').map(part => part.charAt(0)).join('');
    }

    formatTraitName(trait) {
        return trait.charAt(0).toUpperCase() + trait.slice(1);
    }

    getRecommendationClass(status) {
        return status.toLowerCase().replace(/\s+/g, '-');
    }

    getScoreColor(score) {
        if (score >= 0.8) return '#10b981';
        if (score >= 0.6) return '#3b82f6';
        if (score >= 0.4) return '#f59e0b';
        return '#ef4444';
    }

    createRadarChart(candidate) {
        const canvasId = `radarChart-${candidate.candidate_info.id}`;
        const canvas = document.getElementById(canvasId);
        
        if (!canvas) {
            console.warn(`Canvas not found for candidate: ${candidate.candidate_info.id}`);
            return;
        }

        const ctx = canvas.getContext('2d');
        const personalityTraits = candidate.candidate_info.personality_traits;

        // The Big Five traits in order (using initials for better visibility)
        const traitLabels = ['O', 'C', 'E', 'A', 'N'];
        const traitFullNames = ['Openness', 'Conscientiousness', 'Extraversion', 'Agreeableness', 'Neuroticism'];
        
        // Extract values and convert to 0-100 scale
        const values = traitFullNames.map(trait => {
            const traitKey = trait.toLowerCase();
            let value = personalityTraits[traitKey];
            
            // Try alternative key formats if not found
            if (value === undefined) {
                const alternativeKeys = [
                    traitKey.replace('ness', ''),
                    traitKey.replace(' ', '_'),
                    trait.toLowerCase().replace(' ', '_')
                ];
                
                for (const altKey of alternativeKeys) {
                    if (personalityTraits[altKey] !== undefined) {
                        value = personalityTraits[altKey];
                        break;
                    }
                }
            }
            
            return value !== undefined ? (value * 100) : 50; // Default to 50 if not found
        });

        const radarChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: traitLabels,
                datasets: [{
                    label: 'Big Five Profile',
                    data: values,
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(99, 102, 241, 1)',
                    pointBorderColor: 'rgba(99, 102, 241, 1)',
                    pointRadius: 3,
                    pointHoverRadius: 4,
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    borderColor: 'rgba(99, 102, 241, 0.8)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Big Five Profile',
                        font: {
                            size: 12,
                            weight: 'bold'
                        },
                        padding: {
                            bottom: 10
                        }
                    },
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const fullName = traitFullNames[context.dataIndex];
                                return `${fullName}: ${context.parsed.r.toFixed(0)}%`;
                            }
                        }
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        min: 0,
                        max: 100,
                        ticks: {
                            stepSize: 20,
                            font: {
                                size: 8
                            },
                            callback: function(value) {
                                return value + '%';
                            }
                        },
                        pointLabels: {
                            font: {
                                size: 9
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        angleLines: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                },
                elements: {
                    point: {
                        borderWidth: 1
                    }
                },
                // Disable animations for better performance
                animation: {
                    duration: 0
                },
                transitions: {
                    active: {
                        animation: {
                            duration: 0
                        }
                    }
                }
            }
        });

        // Store chart reference for cleanup if needed
        if (!this.radarCharts) {
            this.radarCharts = {};
        }
        this.radarCharts[candidate.candidate_info.id] = radarChart;
    }

    cleanupRadarCharts() {
        if (this.radarCharts) {
            Object.values(this.radarCharts).forEach(chart => {
                if (chart && typeof chart.destroy === 'function') {
                    chart.destroy();
                }
            });
            this.radarCharts = {};
        }
    }

    showCandidateDetails(candidateId) {
        const candidate = this.data.candidates_analysis.find(c => c.candidate_info.id === candidateId);
        if (!candidate) return;

        const modal = document.getElementById('modal-overlay');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');

        modalTitle.textContent = `${candidate.candidate_info.name} - Detailed Analysis`;

        modalBody.innerHTML = `
            <div class="modal-section">
                <h4><i class="fas fa-user"></i> Candidate Information</h4>
                <div class="traits-grid">
                    ${Object.entries(candidate.candidate_info.personality_traits).map(([trait, value]) => `
                        <div class="trait-card">
                            <h5>${this.formatTraitName(trait)}</h5>
                            <div class="value">${(value * 100).toFixed(0)}%</div>
                        </div>
                    `).join('')}
                </div>
            </div>

            <div class="modal-section">
                <h4><i class="fas fa-chart-line"></i> Compatibility Analysis</h4>
                <div class="insights-grid">
                    <div class="insight-item">
                        <h6>Overall Compatibility</h6>
                        <p style="font-size: 1.5rem; font-weight: 700; color: var(--primary-color);">
                            ${(candidate.ai_analysis.compatibility_score * 100).toFixed(1)}%
                        </p>
                    </div>
                </div>
            </div>

            <div class="ai-insights">
                <h5><i class="fas fa-brain"></i> AI Analysis Summary</h5>
                <p style="margin-bottom: 1rem; opacity: 0.9;">${candidate.ai_analysis.summary}</p>
                <div class="insights-grid">
                    <div class="insight-item">
                        <h6>Confidence Level</h6>
                        <p>${(candidate.ai_analysis.confidence_level * 100).toFixed(0)}%</p>
                    </div>
                </div>
            </div>

            <div class="modal-section">
                <h4><i class="fas fa-lightbulb"></i> Strengths</h4>
                <ul style="list-style: disc; margin-left: 1rem;">
                    ${candidate.ai_analysis.strengths.map(strength => 
                        `<li style="margin-bottom: 0.5rem;">${strength}</li>`
                    ).join('')}
                </ul>
            </div>

            <div class="modal-section">
                <h4><i class="fas fa-exclamation-triangle"></i> Areas of Consideration</h4>
                <ul style="list-style: disc; margin-left: 1rem;">
                    ${candidate.ai_analysis.concerns.map(concern => 
                        `<li style="margin-bottom: 0.5rem;">${concern}</li>`
                    ).join('')}
                </ul>
            </div>

            <div class="modal-section">
                <h4><i class="fas fa-recommendations"></i> Recommendations</h4>
                <ul style="list-style: disc; margin-left: 1rem;">
                    ${candidate.ai_analysis.recommendations.map(recommendation => 
                        `<li style="margin-bottom: 0.5rem;">${recommendation}</li>`
                    ).join('')}
                </ul>
            </div>
        `;

        modal.classList.add('active');
    }

    initEventListeners() {
        // Modal close handlers
        const modalOverlay = document.getElementById('modal-overlay');
        const modalClose = document.getElementById('modal-close');

        modalClose.addEventListener('click', () => {
            modalOverlay.classList.remove('active');
        });

        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) {
                modalOverlay.classList.remove('active');
            }
        });

        // Filter and sort handlers
        const sortSelect = document.getElementById('sort-select');
        const filterSelect = document.getElementById('filter-select');

        sortSelect.addEventListener('change', () => {
            this.sortCandidates(sortSelect.value);
            this.renderCandidates();
        });

        filterSelect.addEventListener('change', () => {
            this.filterCandidates(filterSelect.value);
            this.renderCandidates();
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                modalOverlay.classList.remove('active');
            }
        });
    }

    sortCandidates(sortBy) {
        switch (sortBy) {
            case 'compatibility':
                this.filteredCandidates.sort((a, b) => 
                    b.ai_analysis.compatibility_score - a.ai_analysis.compatibility_score
                );
                break;
            case 'name':
                this.filteredCandidates.sort((a, b) => 
                    a.candidate_info.name.localeCompare(b.candidate_info.name)
                );
                break;
            case 'recommendation':
                const recommendationOrder = {
                    'HIGHLY RECOMMENDED': 4,
                    'RECOMMENDED': 3,
                    'CONDITIONALLY RECOMMENDED': 2,
                    'NOT RECOMMENDED': 1
                };
                this.filteredCandidates.sort((a, b) => 
                    recommendationOrder[b.overall_recommendation.status] - 
                    recommendationOrder[a.overall_recommendation.status]
                );
                break;
        }
    }

    filterCandidates(filterBy) {
        if (filterBy === 'all') {
            this.filteredCandidates = [...this.data.candidates_analysis];
        } else {
            this.filteredCandidates = this.data.candidates_analysis.filter(
                candidate => candidate.overall_recommendation.status === filterBy
            );
        }
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new TeamCompatibilityDashboard();
}); 