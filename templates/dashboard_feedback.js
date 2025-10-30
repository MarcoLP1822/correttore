/**
 * Dashboard Feedback - JavaScript
 * FASE 6 Task 6.5 - Sistema visualizzazione statistiche feedback
 */

// Global state
let feedbackData = [];
let learnedCorrections = [];
let charts = {};

// Initialize dashboard on load
document.addEventListener('DOMContentLoaded', function() {
    console.log('📊 Initializing Feedback Dashboard...');
    loadDashboardData();
});

/**
 * Load all dashboard data
 */
async function loadDashboardData() {
    try {
        // Load from localStorage (frontend storage)
        const storedFeedback = localStorage.getItem('correction_feedback');
        if (storedFeedback) {
            feedbackData = JSON.parse(storedFeedback);
            console.log(`✅ Loaded ${feedbackData.length} feedback items from localStorage`);
        }
        
        // Load learned corrections from custom_corrections.txt metadata
        // (In production, this would be loaded from backend API)
        loadLearnedCorrections();
        
        // Render all components
        updateStatCards();
        renderTimelineChart();
        renderCategoryChart();
        renderLearnedTable();
        renderContestedTable();
        renderRecentTable();
        updateAdvancedStats();
        updateTimestamp();
        
        console.log('✅ Dashboard loaded successfully');
    } catch (error) {
        console.error('❌ Error loading dashboard:', error);
    }
}

/**
 * Update stat cards with current data
 */
function updateStatCards() {
    const total = feedbackData.length;
    const correct = feedbackData.filter(f => f.feedback === 'corretta').length;
    const error = feedbackData.filter(f => f.feedback === 'errore').length;
    const learned = learnedCorrections.length;
    
    document.getElementById('totalFeedback').textContent = total;
    document.getElementById('correctFeedback').textContent = correct;
    document.getElementById('errorFeedback').textContent = error;
    document.getElementById('learnedCorrections').textContent = learned;
}

/**
 * Render timeline chart (last 30 days)
 */
function renderTimelineChart() {
    const canvas = document.getElementById('timelineChart');
    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart if any
    if (charts.timeline) {
        charts.timeline.destroy();
    }
    
    // Group feedback by date (last 30 days)
    const last30Days = getLast30Days();
    const correctByDate = {};
    const errorByDate = {};
    
    last30Days.forEach(date => {
        correctByDate[date] = 0;
        errorByDate[date] = 0;
    });
    
    feedbackData.forEach(feedback => {
        const date = new Date(feedback.timestamp).toISOString().split('T')[0];
        if (last30Days.includes(date)) {
            if (feedback.feedback === 'corretta') {
                correctByDate[date]++;
            } else {
                errorByDate[date]++;
            }
        }
    });
    
    charts.timeline = new Chart(ctx, {
        type: 'line',
        data: {
            labels: last30Days.map(d => {
                const date = new Date(d);
                return `${date.getDate()}/${date.getMonth() + 1}`;
            }),
            datasets: [
                {
                    label: '✅ Correzioni Approvate',
                    data: last30Days.map(d => correctByDate[d]),
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: '❌ False Positive',
                    data: last30Days.map(d => errorByDate[d]),
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

/**
 * Render category consensus chart
 */
function renderCategoryChart() {
    const canvas = document.getElementById('categoryChart');
    const ctx = canvas.getContext('2d');
    
    if (charts.category) {
        charts.category.destroy();
    }
    
    // Group by category and calculate consensus
    const categories = ['SPELLING', 'GRAMMAR', 'STYLE', 'VOCABULARY', 'OTHER'];
    const consensusData = categories.map(cat => {
        const catFeedback = feedbackData.filter(f => f.category === cat);
        if (catFeedback.length === 0) return 0;
        
        const correct = catFeedback.filter(f => f.feedback === 'corretta').length;
        return (correct / catFeedback.length) * 100;
    });
    
    charts.category = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: categories.map(c => {
                const emoji = {
                    'SPELLING': '📝',
                    'GRAMMAR': '📚',
                    'STYLE': '🎨',
                    'VOCABULARY': '📖',
                    'OTHER': '🔧'
                };
                return emoji[c] + ' ' + c;
            }),
            datasets: [{
                label: 'Tasso di Consenso (%)',
                data: consensusData,
                backgroundColor: [
                    'rgba(59, 130, 246, 0.8)',
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(236, 72, 153, 0.8)',
                    'rgba(107, 114, 128, 0.8)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
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
                }
            }
        }
    });
}

/**
 * Render learned corrections table
 */
function renderLearnedTable() {
    const tbody = document.getElementById('learnedTableBody');
    const badge = document.getElementById('learnedBadge');
    
    badge.textContent = learnedCorrections.length;
    
    if (learnedCorrections.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-state">Nessuna correzione appresa ancora</td></tr>';
        return;
    }
    
    tbody.innerHTML = learnedCorrections.map(correction => {
        const date = new Date(correction.timestamp);
        const consensus = Math.round((correction.correctCount / correction.totalFeedback) * 100);
        
        return `
            <tr>
                <td><strong>${correction.original}</strong></td>
                <td>${correction.corrected}</td>
                <td>${correction.totalFeedback}</td>
                <td>
                    <div class="consensus-bar">
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${consensus}%"></div>
                        </div>
                        <span>${consensus}%</span>
                    </div>
                </td>
                <td>${date.toLocaleDateString('it-IT')}</td>
            </tr>
        `;
    }).join('');
}

/**
 * Render contested corrections table
 */
function renderContestedTable() {
    const tbody = document.getElementById('contestedTableBody');
    const badge = document.getElementById('contestedBadge');
    
    // Find corrections with mixed feedback (contested)
    const correctionGroups = {};
    
    feedbackData.forEach(feedback => {
        const key = `${feedback.originalText}::${feedback.correctedText}`;
        if (!correctionGroups[key]) {
            correctionGroups[key] = {
                original: feedback.originalText,
                corrected: feedback.correctedText,
                correct: 0,
                error: 0
            };
        }
        
        if (feedback.feedback === 'corretta') {
            correctionGroups[key].correct++;
        } else {
            correctionGroups[key].error++;
        }
    });
    
    // Filter contested (both correct and error feedback)
    const contested = Object.values(correctionGroups)
        .filter(g => g.correct > 0 && g.error > 0)
        .sort((a, b) => (b.correct + b.error) - (a.correct + a.error))
        .slice(0, 10);
    
    badge.textContent = contested.length;
    
    if (contested.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-state">Nessuna correzione contestata</td></tr>';
        return;
    }
    
    tbody.innerHTML = contested.map(item => `
        <tr>
            <td>${item.original.substring(0, 50)}${item.original.length > 50 ? '...' : ''}</td>
            <td>${item.corrected.substring(0, 50)}${item.corrected.length > 50 ? '...' : ''}</td>
            <td><span class="feedback-badge feedback-corretta">${item.correct}</span></td>
            <td><span class="feedback-badge feedback-errore">${item.error}</span></td>
            <td>
                <button class="action-btn" onclick="reviewCorrection('${item.original}', '${item.corrected}')">
                    Rivedi
                </button>
            </td>
        </tr>
    `).join('');
}

/**
 * Render recent feedback table
 */
function renderRecentTable() {
    const tbody = document.getElementById('recentTableBody');
    
    if (feedbackData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Nessun feedback disponibile</td></tr>';
        return;
    }
    
    // Sort by timestamp descending
    const recent = [...feedbackData]
        .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
        .slice(0, 50);
    
    tbody.innerHTML = recent.map(feedback => {
        const date = new Date(feedback.timestamp);
        const category = feedback.category || 'OTHER';
        
        return `
            <tr>
                <td>${date.toLocaleString('it-IT')}</td>
                <td>${feedback.documentName || 'N/A'}</td>
                <td>${feedback.originalText.substring(0, 40)}${feedback.originalText.length > 40 ? '...' : ''}</td>
                <td>${feedback.correctedText.substring(0, 40)}${feedback.correctedText.length > 40 ? '...' : ''}</td>
                <td><span class="category-badge category-${category}">${category}</span></td>
                <td><span class="feedback-badge feedback-${feedback.feedback}">${feedback.feedback === 'corretta' ? '✅ Corretta' : '❌ Errore'}</span></td>
            </tr>
        `;
    }).join('');
}

/**
 * Update advanced statistics
 */
function updateAdvancedStats() {
    // Consensus rate
    const correct = feedbackData.filter(f => f.feedback === 'corretta').length;
    const total = feedbackData.length;
    const consensusRate = total > 0 ? Math.round((correct / total) * 100) : 0;
    document.getElementById('consensusRate').textContent = consensusRate + '%';
    
    // Avg feedback per day
    const days = getLast30Days().length;
    const avgPerDay = total > 0 ? (total / days).toFixed(1) : 0;
    document.getElementById('avgFeedbackPerDay').textContent = avgPerDay;
    
    // Top category
    const categoryCount = {};
    feedbackData.forEach(f => {
        const cat = f.category || 'OTHER';
        categoryCount[cat] = (categoryCount[cat] || 0) + 1;
    });
    
    const topCat = Object.entries(categoryCount)
        .sort((a, b) => b[1] - a[1])[0];
    document.getElementById('topCategory').textContent = topCat ? topCat[0] : 'N/A';
    
    // Last update
    if (feedbackData.length > 0) {
        const lastFeedback = [...feedbackData]
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))[0];
        const lastDate = new Date(lastFeedback.timestamp);
        document.getElementById('lastUpdate').textContent = lastDate.toLocaleString('it-IT');
    }
}

/**
 * Load learned corrections (simulated - would come from backend)
 */
function loadLearnedCorrections() {
    // Simulate learned corrections from feedback consensus
    const correctionGroups = {};
    
    feedbackData.forEach(feedback => {
        const key = feedback.originalText.toLowerCase();
        if (!correctionGroups[key]) {
            correctionGroups[key] = {
                original: feedback.originalText,
                corrected: feedback.correctedText,
                correct: 0,
                error: 0,
                timestamp: feedback.timestamp
            };
        }
        
        if (feedback.feedback === 'corretta') {
            correctionGroups[key].correct++;
        } else {
            correctionGroups[key].error++;
        }
    });
    
    // Filter learned (>= 3 feedback with 75%+ consensus)
    learnedCorrections = Object.values(correctionGroups)
        .filter(g => {
            const total = g.correct + g.error;
            const consensus = g.correct / total;
            return total >= 3 && consensus >= 0.75;
        })
        .map(g => ({
            original: g.original,
            corrected: g.corrected,
            totalFeedback: g.correct + g.error,
            correctCount: g.correct,
            timestamp: g.timestamp
        }))
        .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
}

/**
 * Apply filters to recent table
 */
function applyFilters() {
    const categoryFilter = document.getElementById('filterCategory').value;
    const feedbackFilter = document.getElementById('filterFeedback').value;
    
    let filtered = [...feedbackData];
    
    if (categoryFilter !== 'all') {
        filtered = filtered.filter(f => f.category === categoryFilter);
    }
    
    if (feedbackFilter !== 'all') {
        filtered = filtered.filter(f => f.feedback === feedbackFilter);
    }
    
    // Temporarily replace feedbackData for rendering
    const original = feedbackData;
    feedbackData = filtered;
    renderRecentTable();
    feedbackData = original;
}

/**
 * Export all data as JSON
 */
function exportAllData() {
    const data = {
        exportDate: new Date().toISOString(),
        totalFeedback: feedbackData.length,
        learnedCorrections: learnedCorrections,
        feedback: feedbackData,
        statistics: {
            consensusRate: document.getElementById('consensusRate').textContent,
            avgFeedbackPerDay: document.getElementById('avgFeedbackPerDay').textContent,
            topCategory: document.getElementById('topCategory').textContent
        }
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `feedback_export_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    console.log('📥 Exported feedback data');
}

/**
 * Refresh dashboard
 */
function refreshDashboard() {
    console.log('🔄 Refreshing dashboard...');
    loadDashboardData();
}

/**
 * Clear all feedback with confirmation
 */
function clearAllFeedback() {
    if (confirm('⚠️ Sei sicuro di voler eliminare tutti i feedback? Questa azione non può essere annullata.')) {
        localStorage.removeItem('correction_feedback');
        feedbackData = [];
        learnedCorrections = [];
        
        console.log('🗑️ All feedback cleared');
        loadDashboardData();
        
        alert('✅ Tutti i feedback sono stati eliminati.');
    }
}

/**
 * Review specific correction
 */
function reviewCorrection(original, corrected) {
    alert(`📋 Revisione Correzione:\n\nOriginale: ${original}\nCorrezione: ${corrected}\n\nFunzionalità di revisione dettagliata sarà implementata in una versione futura.`);
}

/**
 * Update footer timestamp
 */
function updateTimestamp() {
    const now = new Date();
    document.getElementById('footerTimestamp').textContent = now.toLocaleString('it-IT');
}

/**
 * Helper: Get last 30 days as array of date strings
 */
function getLast30Days() {
    const dates = [];
    const today = new Date();
    
    for (let i = 29; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        dates.push(date.toISOString().split('T')[0]);
    }
    
    return dates;
}
