// Configuration
const API_BASE_URL = 'http://localhost:5000/api';
let horsesData = [];
let chart = null;
let pdfChart = null;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    initializeHorses();
    setupTabs();
    loadDashboard();
});

// ============================================
// TAB NAVIGATION
// ============================================

function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            
            tabButtons.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            this.classList.add('active');
            document.getElementById(tabName).classList.add('active');
            
            if (tabName === 'horses') {
                loadHorsesMaster();
            } else if (tabName === 'dashboard') {
                loadDashboard();
            }
        });
    });
}

// ============================================
// NEW: LOAD RACE FROM PDF
// ============================================

async function loadRaceFromPDF() {
    const fileInput = document.getElementById('pdfFile');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Veuillez sélectionner un fichier PDF');
        return;
    }
    
    showStatus('Chargement de la course depuis PDF...', 'loading');
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_BASE_URL}/load-race-from-pdf`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            showStatus(`Erreur: ${data.error}`, 'error');
            return;
        }
        
        // Display race info
        const raceInfo = data.race_info;
        const raceInfoHTML = `
            <div class="info-row">
                <strong>Date:</strong> ${raceInfo.race_date || 'N/A'}
            </div>
            <div class="info-row">
                <strong>Hippodrome:</strong> ${raceInfo.hippodrome || 'N/A'}
            </div>
            <div class="info-row">
                <strong>Distance:</strong> ${raceInfo.distance || 'N/A'} m
            </div>
            <div class="info-row">
                <strong>Type:</strong> ${raceInfo.race_type || 'N/A'}
            </div>
            <div class="info-row">
                <strong>Nom:</strong> ${raceInfo.race_name || 'N/A'}
            </div>
            <div class="info-row">
                <strong>Concurrents:</strong> ${raceInfo.num_competitors || 'N/A'}
            </div>
            <div class="info-row">
                <strong>Arrivée:</strong> ${raceInfo.arrival ? raceInfo.arrival.join(' - ') : 'N/A'}
            </div>
        `;
        document.getElementById('raceInfo').innerHTML = raceInfoHTML;
        
        // Display predictions
        const tbody = document.getElementById('pdfPredictionsTable');
        tbody.innerHTML = '';
        
        data.predictions.forEach(pred => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${pred.rank}</strong></td>
                <td>${pred.horse_number}</td>
                <td><strong>${pred.horse_name}</strong></td>
                <td>${(pred.predicted_probability * 100).toFixed(2)}%</td>
                <td>${(pred.odds_probability * 100).toFixed(2)}%</td>
            `;
            tbody.appendChild(row);
        });
        
        // Draw chart
        if (data.predictions.length > 0) {
            drawPDFChart(data.predictions);
        }
        
        document.getElementById('pdfResults').classList.remove('hidden');
        showStatus(`✅ ${data.horses_imported} chevaux importés! ${data.message}`, 'success');
        
    } catch (error) {
        console.error('Error:', error);
        showStatus(`Erreur: ${error.message}`, 'error');
    }
}

function drawPDFChart(predictions) {
    const ctx = document.getElementById('pdfChart');
    const container = document.getElementById('pdfChartContainer');
    
    const labels = predictions.map(p => p.horse_name.substring(0, 15));
    const data = predictions.map(p => p.predicted_probability * 100);
    const colors = predictions.map(p => {
        const prob = p.predicted_probability * 100;
        if (prob > 15) return 'rgba(22, 163, 74, 0.8)';
        if (prob > 8) return 'rgba(234, 88, 12, 0.8)';
        return 'rgba(220, 38, 38, 0.8)';
    });
    
    // Safely destroy previous chart
    if (pdfChart && typeof pdfChart.destroy === 'function') {
        try {
            pdfChart.destroy();
        } catch (e) {
            console.warn('Error destroying chart:', e);
        }
    }
    
    container.style.display = 'block';
    pdfChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Probabilité (%)',
                data: data,
                backgroundColor: colors,
                borderColor: colors.map(c => c.replace('0.8', '1')),
                borderWidth: 2,
                borderRadius: 8,
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: true } },
            scales: { x: { min: 0, max: 100, ticks: { callback: v => v + '%' } } }
        }
    });
}

function resetPDFForm() {
    document.getElementById('pdfFile').value = '';
    document.getElementById('pdfResults').classList.add('hidden');
}

// ============================================
// MANUAL HORSE MANAGEMENT
// ============================================

function initializeHorses() {
    horsesData = [
        {
            number: 1,
            name: '',
            description: '',
            odds: ''
        }
    ];
    renderHorsesTable();
}

function renderHorsesTable() {
    const tbody = document.getElementById('horsesTableBody');
    tbody.innerHTML = '';
    
    horsesData.forEach((horse, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><input type="number" value="${horse.number}" onchange="updateHorse(${index}, 'number', this.value)"></td>
            <td><input type="text" value="${horse.name}" onchange="updateHorse(${index}, 'name', this.value)"></td>
            <td><textarea onchange="updateHorse(${index}, 'description', this.value)">${horse.description}</textarea></td>
            <td><input type="text" value="${horse.odds}" placeholder="ex: 77/1" onchange="updateHorse(${index}, 'odds', this.value)"></td>
            <td>
                <button class="btn btn-danger btn-small" onclick="removeHorse(${index})">Supprimer</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function updateHorse(index, field, value) {
    if (index >= 0 && index < horsesData.length) {
        horsesData[index][field] = value;
    }
}

function addHorse() {
    horsesData.push({
        number: horsesData.length + 1,
        name: '',
        description: '',
        odds: '10/1'
    });
    renderHorsesTable();
}

function removeHorse(index) {
    if (confirm('Supprimer ce cheval?')) {
        horsesData.splice(index, 1);
        renderHorsesTable();
    }
}

function removeLastHorse() {
    if (horsesData.length > 0) {
        horsesData.pop();
        renderHorsesTable();
    }
}

// ============================================
// MANUAL PREDICTION
// ============================================

async function makePrediction() {
    if (horsesData.length === 0) {
        showStatus('Veuillez ajouter au moins un cheval', 'error');
        return;
    }
    
    showStatus('Génération du pronostic...', 'loading');
    
    try {
        const payload = {
            race_date: document.getElementById('raceDate').value || new Date().toISOString().split('T')[0],
            hippodrome: document.getElementById('hippodrome').value,
            distance: parseInt(document.getElementById('distance').value) || null,
            race_type: document.getElementById('raceType').value,
            conditions: document.getElementById('conditions').value,
            horses: horsesData
        };
        
        const response = await fetch(`${API_BASE_URL}/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error);
        }
        
        const data = await response.json();
        displayResults(data);
        showStatus('✅ Pronostic généré!', 'success');
        
    } catch (error) {
        console.error('Error:', error);
        showStatus(`❌ Erreur: ${error.message}`, 'error');
    }
}

function displayResults(data) {
    document.getElementById('winnerName').textContent = data.analysis.predicted_winner || '-';
    document.getElementById('winnerProb').textContent = 
        `${(data.analysis.winner_confidence * 100).toFixed(2)}% de chance`;
    
    document.getElementById('podium').textContent = 
        (data.analysis.top_3 || []).join(' • ') || '-';
    
    const tbody = document.getElementById('resultsTableBody');
    tbody.innerHTML = '';
    
    data.predictions.forEach(pred => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${pred.rank}</strong></td>
            <td>${pred.horse_number}</td>
            <td><strong>${pred.horse_name}</strong></td>
            <td>${pred.decimal_odds > 0 ? pred.decimal_odds.toFixed(2) : '-'}</td>
            <td>${(pred.odds_probability * 100).toFixed(2)}%</td>
            <td><strong>${(pred.predicted_probability * 100).toFixed(2)}%</strong></td>
            <td>${getConfidenceBar(pred.predicted_probability)}</td>
        `;
        tbody.appendChild(row);
    });
    
    drawPredictionsChart(data.predictions);
    document.getElementById('resultsContainer').classList.remove('hidden');
}

function getConfidenceBar(probability) {
    const percentage = Math.round(probability * 100);
    const barWidth = Math.min(percentage, 100);
    let color = '#16a34a';
    if (percentage < 30) color = '#dc2626';
    else if (percentage < 50) color = '#ea580c';
    
    return `
        <div style="width: 100%; background: #e2e8f0; border-radius: 4px; height: 20px; overflow: hidden;">
            <div style="width: ${barWidth}%; background: ${color}; height: 100%; display: flex; align-items: center; justify-content: center; color: white; font-size: 0.8em; font-weight: bold;">
                ${percentage}%
            </div>
        </div>
    `;
}

function drawPredictionsChart(predictions) {
    const ctx = document.getElementById('predictionsChart').getContext('2d');
    
    const labels = predictions.map(p => p.horse_name.substring(0, 15));
    const data = predictions.map(p => p.predicted_probability * 100);
    const colors = predictions.map(p => {
        const prob = p.predicted_probability * 100;
        if (prob > 15) return 'rgba(22, 163, 74, 0.8)';
        if (prob > 8) return 'rgba(234, 88, 12, 0.8)';
        return 'rgba(220, 38, 38, 0.8)';
    });
    
    if (chart && typeof chart.destroy === 'function') {
        try {
            chart.destroy();
        } catch (e) {
            console.warn('Error destroying chart:', e);
        }
    }
    
    chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Probabilité (%)',
                data: data,
                backgroundColor: colors,
                borderColor: colors.map(c => c.replace('0.8', '1')),
                borderWidth: 2,
                borderRadius: 8,
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            plugins: { legend: { display: true } },
            scales: { x: { min: 0, max: 100, ticks: { callback: v => v + '%' } } }
        }
    });
}

function downloadResults() {
    const results = document.getElementById('resultsTableBody');
    const date = new Date().toISOString().split('T')[0];
    const hippodrome = document.getElementById('hippodrome').value;
    
    let csv = 'Rang,Numéro,Nom,Cotes (Décimal),Probabilité Marché,Prédiction,Confiance\n';
    results.querySelectorAll('tr').forEach(row => {
        const cells = row.querySelectorAll('td');
        const rowData = Array.from(cells).slice(0, 7).map(cell => `"${cell.textContent.trim()}"`);
        csv += rowData.join(',') + '\n';
    });
    
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `pronostic_${hippodrome}_${date}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function resetForm() {
    document.getElementById('resultsContainer').classList.add('hidden');
    initializeHorses();
    document.getElementById('raceDate').value = new Date().toISOString().split('T')[0];
}

// ============================================
// HORSES MASTER
// ============================================

async function loadHorsesMaster() {
    showStatus('Chargement des chevaux...', 'loading');
    
    try {
        const response = await fetch(`${API_BASE_URL}/horses`);
        if (!response.ok) throw new Error('Erreur API');
        const data = await response.json();
        
        const totalRaces = data.horses.reduce((sum, h) => sum + (h.total_races || 0), 0);
        const totalWins = data.horses.reduce((sum, h) => sum + (h.wins || 0), 0);
        const totalPodiums = data.horses.reduce((sum, h) => sum + (h.podiums || 0), 0);
        
        document.getElementById('totalHorsesMaster').textContent = data.total_horses;
        document.getElementById('totalRacesTracked').textContent = totalRaces;
        document.getElementById('totalWins').textContent = totalWins;
        document.getElementById('totalPodiums').textContent = totalPodiums;
        
        const tbody = document.getElementById('horsesMasterBody');
        if (data.horses.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center;">Aucun cheval en BD</td></tr>';
            showStatus('✅ Aucun cheval importé pour le moment', 'success');
            return;
        }
        
        tbody.innerHTML = data.horses.map(horse => `
            <tr>
                <td><strong>${horse.horse_name}</strong></td>
                <td>${horse.jockey || '-'}</td>
                <td>${horse.trainer || '-'}</td>
                <td>${horse.total_races}</td>
                <td><strong>${horse.wins}</strong></td>
                <td><strong>${horse.podiums}</strong></td>
                <td>${horse.avg_position ? horse.avg_position.toFixed(2) : '-'}</td>
            </tr>
        `).join('');
        
        showStatus(`✅ ${data.total_horses} chevaux chargés!`, 'success');
        
    } catch (error) {
        showStatus(`Erreur: ${error.message}`, 'error');
    }
}

// ============================================
// DASHBOARD
// ============================================

async function loadDashboard() {
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard`);
        if (!response.ok) throw new Error('Erreur API');
        const data = await response.json();
        
        // Update metrics
        document.getElementById('dashHorses').textContent = data.total_unique_horses || 0;
        document.getElementById('dashRaces').textContent = data.total_races_tracked || 0;
        document.getElementById('dashWins').textContent = 
            (data.total_unique_horses > 0) ? 
            Math.round((data.total_races_tracked / Math.max(data.total_unique_horses, 1)) * 100) / 100 : 0;
        
        const learning_pct = Math.min(100, Math.round((data.total_races_tracked / 50) * 100));
        document.getElementById('dashLearning').textContent = learning_pct + '%';
        
        // Update learning status
        document.getElementById('learningHorses').textContent = data.total_unique_horses || 0;
        document.getElementById('learningRaces').textContent = data.total_races_tracked || 0;
        document.getElementById('learningResults').textContent = data.total_races_tracked || 0;
        
        let quality = 'Faible - Importer plus de PDFs';
        if (data.total_races_tracked >= 100) quality = 'Excellente - Modèle bien entraîné';
        else if (data.total_races_tracked >= 50) quality = 'Bonne - Continuer les imports';
        else if (data.total_races_tracked >= 20) quality = 'Acceptable - Importer plus de courses';
        
        document.getElementById('dataQuality').textContent = quality;
        
        // Recommendations
        const recs = [];
        if (data.total_races_tracked < 20) recs.push('Importer au moins 20 courses pour débuter');
        if (data.total_races_tracked < 50) recs.push('Continuer l\'import de PDFs pour améliorer l\'apprentissage');
        if (data.total_races_tracked < 100) recs.push('Atteindre 100 courses pour un modèle fiable');
        if (recs.length === 0) recs.push('Modèle bien alimenté - Utiliser pour les prédictions');
        
        document.getElementById('recommendations').innerHTML = recs.map(r => `<li>${r}</li>`).join('');
        
        document.getElementById('dashboardMetrics').classList.remove('hidden');
        
    } catch (error) {
        console.error('Error:', error);
    }
}

// ============================================
// STATUS MESSAGES
// ============================================

function showStatus(message, type = 'info') {
    const statusBar = document.getElementById('statusBar');
    const statusText = document.getElementById('statusText');
    
    statusBar.className = `status-bar ${type}`;
    statusText.textContent = message;
    
    if (type !== 'loading') {
        setTimeout(() => {
            statusBar.classList.add('hidden');
        }, 5000);
    }
}
