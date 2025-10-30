// ========================================
// REPORT CORREZIONE - JAVASCRIPT
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    initializeTabs();
    initializeErrorGroups();
    initializeFeedbackButtons();
    initializeCharts();
    initializeSorting();
    initializeFiltering();
});

// ========================================
// GESTIONE TABS
// ========================================

function initializeTabs() {
    const tabItems = document.querySelectorAll('.tab-item');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabItems.forEach(tab => {
        tab.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            
            // Rimuovi active da tutti i tabs
            tabItems.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Aggiungi active al tab selezionato
            this.classList.add('active');
            const targetContent = document.getElementById('tab-' + targetTab);
            if (targetContent) {
                targetContent.classList.add('active');
            }
            
            // Scroll to top
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    });
}

// ========================================
// GRUPPI ERRORI COLLASSABILI
// ========================================

function initializeErrorGroups() {
    // Tutti i gruppi iniziano espansi
    const errorGroups = document.querySelectorAll('.error-group');
    errorGroups.forEach(group => {
        group.classList.remove('collapsed');
    });
}

function toggleGroup(groupId) {
    const group = document.getElementById('group-' + groupId).parentElement;
    const toggleIcon = document.getElementById('toggle-' + groupId);
    
    if (group.classList.contains('collapsed')) {
        group.classList.remove('collapsed');
        toggleIcon.textContent = '▼';
    } else {
        group.classList.add('collapsed');
        toggleIcon.textContent = '▶';
    }
}

// ========================================
// PULSANTI FEEDBACK (per versioni future)
// ========================================

function initializeFeedbackButtons() {
    const feedbackButtons = document.querySelectorAll('.btn-feedback');
    
    feedbackButtons.forEach(button => {
        button.addEventListener('click', function() {
            const correctionId = this.getAttribute('data-id');
            const feedbackType = this.classList.contains('btn-correct') ? 'corretta' : 'errore';
            
            saveFeedback(correctionId, feedbackType, this);
        });
    });
}

function saveFeedback(correctionId, feedbackType, button) {
    // Disabilita pulsanti
    const buttons = button.parentElement.querySelectorAll('.btn-feedback');
    buttons.forEach(btn => btn.disabled = true);
    
    // Aggiungi classe feedback per styling
    button.classList.add('feedback-sent');
    
    // Mostra messaggio di conferma
    const confirmMessage = document.createElement('span');
    confirmMessage.textContent = feedbackType === 'corretta' ? '✓ Registrato come corretto' : '✗ Registrato come errore';
    confirmMessage.style.marginLeft = '10px';
    confirmMessage.style.color = feedbackType === 'corretta' ? '#27ae60' : '#e74c3c';
    confirmMessage.style.fontWeight = '600';
    confirmMessage.className = 'feedback-confirmation';
    button.parentElement.appendChild(confirmMessage);
    
    // Salva feedback in localStorage (FASE 6)
    const feedback = {
        id: correctionId,
        type: feedbackType,
        timestamp: new Date().toISOString(),
        documentName: document.title
    };
    
    // Recupera feedback esistenti
    let allFeedback = JSON.parse(localStorage.getItem('correctionFeedback') || '[]');
    allFeedback.push(feedback);
    localStorage.setItem('correctionFeedback', JSON.stringify(allFeedback));
    
    console.log(`✅ Feedback salvato localmente: ${correctionId} = ${feedbackType}`);
    console.log(`📊 Feedback totali: ${allFeedback.length}`);
    
    // TODO FASE 6: Inviare a backend quando disponibile
    // fetch('/api/feedback', {
    //     method: 'POST',
    //     headers: { 'Content-Type': 'application/json' },
    //     body: JSON.stringify(feedback)
    // }).then(response => response.json())
    //   .then(data => console.log('Feedback salvato su server:', data))
    //   .catch(error => console.error('Errore salvataggio feedback:', error));
}

// ========================================
// UTILITY FUNCTIONS
// ========================================

function expandAllGroups() {
    const errorGroups = document.querySelectorAll('.error-group');
    errorGroups.forEach(group => {
        group.classList.remove('collapsed');
        const toggleIcon = group.querySelector('.toggle-icon');
        if (toggleIcon) {
            toggleIcon.textContent = '▼';
        }
    });
}

function collapseAllGroups() {
    const errorGroups = document.querySelectorAll('.error-group');
    errorGroups.forEach(group => {
        group.classList.add('collapsed');
        const toggleIcon = group.querySelector('.toggle-icon');
        if (toggleIcon) {
            toggleIcon.textContent = '▶';
        }
    });
}

// ========================================
// GRAFICI
// ========================================

function initializeCharts() {
    // Inizializza tutti i grafici presenti nella pagina
    renderPieChart();
    renderBarChart();
}

function renderPieChart() {
    const canvas = document.getElementById('chart-pie');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const data = JSON.parse(canvas.getAttribute('data-chart'));
    
    if (!data || !data.labels || !data.values) return;
    
    // Colori per le categorie
    const colors = [
        '#e74c3c', '#f39c12', '#f1c40f', '#27ae60', 
        '#3498db', '#9b59b6', '#34495e', '#1abc9c',
        '#e67e22', '#95a5a6', '#16a085'
    ];
    
    // Calcola totale e percentuali
    const total = data.values.reduce((a, b) => a + b, 0);
    if (total === 0) return;
    
    // Dimensioni
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = Math.min(centerX, centerY) - 40;
    
    // Disegna grafico a torta
    let currentAngle = -Math.PI / 2; // Inizia dall'alto
    
    data.values.forEach((value, index) => {
        const sliceAngle = (value / total) * 2 * Math.PI;
        
        // Disegna slice
        ctx.beginPath();
        ctx.fillStyle = colors[index % colors.length];
        ctx.moveTo(centerX, centerY);
        ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
        ctx.closePath();
        ctx.fill();
        
        // Disegna bordo bianco
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.stroke();
        
        currentAngle += sliceAngle;
    });
    
    // Disegna legenda
    renderLegend(canvas, data.labels, data.values, colors, total);
}

function renderLegend(canvas, labels, values, colors, total) {
    const legendContainer = canvas.nextElementSibling;
    if (!legendContainer || !legendContainer.classList.contains('chart-legend')) return;
    
    legendContainer.innerHTML = '';
    
    labels.forEach((label, index) => {
        const value = values[index];
        const percentage = ((value / total) * 100).toFixed(1);
        
        const legendItem = document.createElement('div');
        legendItem.className = 'legend-item';
        legendItem.innerHTML = `
            <span class="legend-color" style="background: ${colors[index % colors.length]}"></span>
            <span class="legend-label">${label}</span>
            <span class="legend-value">${value} (${percentage}%)</span>
        `;
        
        legendContainer.appendChild(legendItem);
    });
}

function renderBarChart() {
    const canvas = document.getElementById('chart-bar');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const data = JSON.parse(canvas.getAttribute('data-chart'));
    
    if (!data || !data.labels || !data.values) return;
    
    // Colori per le barre
    const barColors = ['#3498db', '#e74c3c'];
    
    // Dimensioni
    const padding = 40;
    const chartWidth = canvas.width - padding * 2;
    const chartHeight = canvas.height - padding * 2;
    
    // Trova valore massimo
    const maxValue = Math.max(...data.values.flat());
    const scale = chartHeight / (maxValue * 1.1); // 10% extra per spacing
    
    // Calcola larghezza barre
    const numGroups = data.labels.length;
    const groupWidth = chartWidth / numGroups;
    const barWidth = groupWidth / (data.values.length + 1);
    
    // Disegna assi
    ctx.strokeStyle = '#95a5a6';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, canvas.height - padding);
    ctx.lineTo(canvas.width - padding, canvas.height - padding);
    ctx.stroke();
    
    // Disegna barre
    data.labels.forEach((label, groupIndex) => {
        const groupX = padding + groupIndex * groupWidth;
        
        data.values.forEach((series, seriesIndex) => {
            const value = series[groupIndex];
            const barHeight = value * scale;
            const barX = groupX + seriesIndex * barWidth + barWidth / 2;
            const barY = canvas.height - padding - barHeight;
            
            // Disegna barra
            ctx.fillStyle = barColors[seriesIndex % barColors.length];
            ctx.fillRect(barX, barY, barWidth, barHeight);
            
            // Disegna valore sopra la barra
            ctx.fillStyle = '#2c3e50';
            ctx.font = '12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(value, barX + barWidth / 2, barY - 5);
        });
        
        // Disegna etichetta
        ctx.fillStyle = '#2c3e50';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(label, groupX + groupWidth / 2, canvas.height - padding + 20);
    });
}

// ========================================
// SORTING TABLES
// ========================================

function initializeSorting() {
    const sortableHeaders = document.querySelectorAll('.sortable-header');
    
    sortableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const table = this.closest('table');
            const columnIndex = Array.from(this.parentElement.children).indexOf(this);
            const currentSort = this.getAttribute('data-sort') || 'none';
            
            // Toggle sort direction
            const newSort = currentSort === 'asc' ? 'desc' : 'asc';
            
            // Reset all headers
            sortableHeaders.forEach(h => h.setAttribute('data-sort', 'none'));
            this.setAttribute('data-sort', newSort);
            
            sortTable(table, columnIndex, newSort);
        });
    });
}

function sortTable(table, columnIndex, direction) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((rowA, rowB) => {
        const cellA = rowA.cells[columnIndex].textContent.trim();
        const cellB = rowB.cells[columnIndex].textContent.trim();
        
        // Try numeric comparison
        const numA = parseFloat(cellA);
        const numB = parseFloat(cellB);
        
        if (!isNaN(numA) && !isNaN(numB)) {
            return direction === 'asc' ? numA - numB : numB - numA;
        }
        
        // String comparison
        return direction === 'asc' 
            ? cellA.localeCompare(cellB)
            : cellB.localeCompare(cellA);
    });
    
    // Re-append rows in sorted order
    rows.forEach(row => tbody.appendChild(row));
}

// ========================================
// FILTERING
// ========================================

function initializeFiltering() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filterValue = this.getAttribute('data-filter');
            const container = this.closest('.filterable-container');
            
            // Update active button
            container.querySelectorAll('.filter-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            this.classList.add('active');
            
            // Apply filter
            applyFilter(container, filterValue);
        });
    });
}

function applyFilter(container, filterValue) {
    const items = container.querySelectorAll('.filterable-item');
    
    items.forEach(item => {
        if (filterValue === 'all' || item.classList.contains(filterValue)) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
}

// ========================================
// FEEDBACK STATISTICS (FASE 6)
// ========================================

function getFeedbackStats() {
    /**
     * Recupera statistiche sui feedback salvati localmente.
     * Returns: {total, corretta, errore, byDocument}
     */
    const allFeedback = JSON.parse(localStorage.getItem('correctionFeedback') || '[]');
    
    const stats = {
        total: allFeedback.length,
        corretta: allFeedback.filter(f => f.type === 'corretta').length,
        errore: allFeedback.filter(f => f.type === 'errore').length,
        byDocument: {}
    };
    
    // Group by document
    allFeedback.forEach(f => {
        if (!stats.byDocument[f.documentName]) {
            stats.byDocument[f.documentName] = { corretta: 0, errore: 0 };
        }
        stats.byDocument[f.documentName][f.type]++;
    });
    
    return stats;
}

function exportFeedbackData() {
    /**
     * Esporta tutti i feedback in formato JSON scaricabile.
     */
    const allFeedback = JSON.parse(localStorage.getItem('correctionFeedback') || '[]');
    
    const dataStr = JSON.stringify(allFeedback, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `feedback_export_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
    console.log(`✅ Esportati ${allFeedback.length} feedback`);
}

function clearAllFeedback() {
    /**
     * Pulisce tutti i feedback salvati (con conferma).
     */
    if (confirm('Sei sicuro di voler cancellare tutti i feedback salvati?')) {
        localStorage.removeItem('correctionFeedback');
        console.log('🗑️ Tutti i feedback cancellati');
        alert('Feedback cancellati con successo');
    }
}

// Log statistiche feedback all'avvio (solo se ci sono feedback)
document.addEventListener('DOMContentLoaded', function() {
    const stats = getFeedbackStats();
    if (stats.total > 0) {
        console.log('📊 Feedback Statistics:');
        console.log(`   Total: ${stats.total}`);
        console.log(`   Corretta: ${stats.corretta} (${(stats.corretta/stats.total*100).toFixed(1)}%)`);
        console.log(`   Errore: ${stats.errore} (${(stats.errore/stats.total*100).toFixed(1)}%)`);
        console.log('   By Document:', stats.byDocument);
    }
});

// ========================================
// ESPORTA FUNZIONI GLOBALI
// ========================================

window.toggleGroup = toggleGroup;
window.expandAllGroups = expandAllGroups;
window.collapseAllGroups = collapseAllGroups;
