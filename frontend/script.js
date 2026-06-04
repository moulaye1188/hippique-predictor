// Hippique Predictor v2 - Frontend Logic

const API_BASE_URL = 'http://localhost:5000/api';
let currentRaceData = null;
let charts = {};

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    setupTabs();
    loadDashboard();
});

// Tab Navigation
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
            
            if (tabName === 'race-analysis' && currentRaceData) {
                createCharts(currentRaceData);
            } else if (tabName === 'horses-master') {
                loadHorsesMaster();
            } else if (tabName === 'dashboard') {
                loadDashboard();
            }
        });
    });
}

// Load Race from PDF
async function loadRaceFromPDF() {
    const fileInput = document.getElementById('pdfFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showStatus('Veuillez sélectionner un fichier PDF', 'warning');
        return;
    }
    
    showStatus('Chargement et analyse du PDF...', 'loading');
    
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
        
        currentRaceData = data;
        
        // Display race info
        displayRaceInfo(data);
        
        // Display pronostics
        displayPronostics(data);
        
        // Display classements
        displayClassements(data);
        
        // Display horses table
        displayHorsesTable(data);
        
        // Display predictions
        displayPredictions(data);
        
        document.getElementById('raceInfoSection').classList.remove('hidden');
        document.getElementById('pronosticsSection').classList.remove('hidden');
        document.getElementById('classementsSection').classList.remove('hidden');
        document.getElementById('horsesTableSection').classList.remove('hidden');
        
        showStatus(`✅ Course chargée! ${data.horses_imported} chevaux, ${Object.keys(data.pronostics || {}).length} pronostics`, 'success');
        
    } catch (error) {
        console.error('Error:', error);
        showStatus(`Erreur: ${error.message}`, 'error');
    }
}

// Display Race Info
function displayRaceInfo(data) {
    const raceInfo = data.race_info || {};
    const html = `
        <div class="info-row">
            <strong>Date</strong>
            ${raceInfo.race_date || 'N/A'}
        </div>
        <div class="info-row">
            <strong>Hippodrome</strong>
            ${raceInfo.hippodrome || 'N/A'}
        </div>
        <div class="info-row">
            <strong>Distance</strong>
            ${raceInfo.distance ? raceInfo.distance + ' m' : 'N/A'}
        </div>
        <div class="info-row">
            <strong>Type</strong>
            ${raceInfo.race_type_bet || raceInfo.race_type || 'N/A'}
        </div>
        <div class="info-row">
            <strong>Course</strong>
            ${raceInfo.race_number ? raceInfo.race_number + 'ème' : 'N/A'}
        </div>
        <div class="info-row">
            <strong>Concurrents</strong>
            ${raceInfo.num_competitors || 'N/A'}
        </div>
        <div class="info-row">
            <strong>Gains</strong>
            ${raceInfo.prize_money_eur ? raceInfo.prize_money_eur + '€' : 'N/A'}
        </div>
        <div class="info-row">
            <strong>Heure</strong>
            ${raceInfo.race_time || 'N/A'}
        </div>
    `;
    document.getElementById('raceInfo').innerHTML = html;
}

// Display Pronostics
function displayPronostics(data) {
    const pronostics = data.pronostics || {};
    let html = '';
    
    for (const [source, horses] of Object.entries(pronostics)) {
        const top3 = horses.slice(0, 3).map(h => `<span class="rank-badge">${h}</span>`).join('');
        html += `
            <div class="pronostic-card">
                <h4>${source}</h4>
                <div class="pronostic-ranking">${top3}</div>
            </div>
        `;
    }
    
    if (html) {
        document.getElementById('pronosticsContainer').innerHTML = html;
    }
}

// Display Classements
function displayClassements(data) {
    const classements = data.classements || {};
    let html = '';
    
    for (const [category, horses] of Object.entries(classements)) {
        const items = horses.slice(0, 5).map(h => `<li>#${h}</li>`).join('');
        html += `
            <div class="classement-card">
                <h4>${category}</h4>
                <ul class="classement-list">${items}</ul>
            </div>
        `;
    }
    
    if (html) {
        document.getElementById('classementsContainer').innerHTML = html;
    }
}

// Display Horses Table
function displayHorsesTable(data) {
    const predictions = data.predictions || [];
    const tbody = document.getElementById('horsesTableBody');
    tbody.innerHTML = '';
    
    predictions.forEach(pred => {
        const row = document.createElement('tr');
        const prob = (pred.predicted_probability * 100).toFixed(2);
        row.innerHTML = `
            <td>${pred.horse_number}</td>
            <td><strong>${pred.horse_name}</strong></td>
            <td>${pred.jockey || '-'}</td>
            <td>${pred.trainer || '-'}</td>
            <td>${pred.weight || '-'}</td>
            <td>${pred.perf || '-'}</td>
            <td>${pred.gains_historical || '-'}</td>
            <td>${pred.odds_paris_turf || '-'}</td>
            <td>${pred.odds_tierce_magazine || '-'}</td>
            <td><strong>${prob}%</strong></td>
        `;
        tbody.appendChild(row);
    });
}

// Display Predictions
function displayPredictions(data) {
    const predictions = data.predictions || [];
    const tbody = document.getElementById('predictionsBody');
    tbody.innerHTML = '';
    
    predictions.forEach((pred, idx) => {
        const prob = (pred.predicted_probability * 100).toFixed(2);
        const confidence = getConfidenceLevel(pred.predicted_probability);
        const rank = pred.predicted_rank || (idx + 1);
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${rank}</strong></td>
            <td>${pred.horse_number}</td>
            <td><strong>${pred.horse_name}</strong></td>
            <td>${prob}%</td>
            <td>${pred.pronostic_rank || '-'}</td>
            <td>${(pred.expert_score * 100).toFixed(0)}%</td>
            <td>${confidence}</td>
        `;
        tbody.appendChild(row);
    });
}

// Create Charts
function createCharts(data) {
    if (!data || !data.predictions) return;
    
    const predictions = data.predictions;
    
    // 1. Probability Distribution Chart
    createProbChart(predictions);
    
    // 2. Expert Score Chart
    createExpertChart(predictions);
    
    // 3. Consensus Chart
    createConsensusChart(data);
}

function createProbChart(predictions) {
    const ctx = document.getElementById('probChart');
    if (!ctx) return;
    
    if (charts.probChart) charts.probChart.destroy();
    
    const labels = predictions.map(p => `#${p.horse_number}`);
    const data = predictions.map(p => (p.predicted_probability * 100).toFixed(1));
    const colors = data.map(d => d > 15 ? '#16a34a' : d > 8 ? '#ea580c' : '#dc2626');
    
    charts.probChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Probabilité (%)',
                data: data,
                backgroundColor: colors,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, max: 100 } }
        }
    });
}

function createExpertChart(predictions) {
    const ctx = document.getElementById('expertChart');
    if (!ctx) return;
    
    if (charts.expertChart) charts.expertChart.destroy();
    
    const labels = predictions.map(p => p.horse_name.substring(0, 10));
    const data = predictions.map(p => (p.expert_score * 100).toFixed(0));
    
    charts.expertChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Score Expert',
                data: data,
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: { legend: { display: true } },
            scales: { r: { beginAtZero: true, max: 100 } }
        }
    });
}

function createConsensusChart(data) {
    const ctx = document.getElementById('consensusChart');
    if (!ctx) return;
    
    if (charts.consensusChart) charts.consensusChart.destroy();
    
    const pronostics = data.pronostics || {};
    const sources = Object.keys(pronostics);
    const labels = data.predictions.map(p => `#${p.horse_number}`).slice(0, 8);
    
    const datasets = sources.map((source, idx) => {
        const colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe'];
        const horseNumbers = pronostics[source] || [];
        const values = data.predictions.map(p => 
            horseNumbers.includes(p.horse_number) ? 1 : 0
        ).slice(0, 8);
        
        return {
            label: source,
            data: values,
            borderColor: colors[idx % colors.length],
            backgroundColor: colors[idx % colors.length],
            tension: 0.4
        };
    });
    
    charts.consensusChart = new Chart(ctx, {
        type: 'line',
        data: { labels: labels, datasets: datasets },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: { legend: { display: true } },
            scales: { y: { beginAtZero: true, max: 1 } }
        }
    });
}

// Horses Master
async function loadHorsesMaster() {
    showStatus('Chargement des chevaux...', 'loading');
    
    try {
        const response = await fetch(`${API_BASE_URL}/horses`);
        if (!response.ok) throw new Error('Erreur API');
        const data = await response.json();
        
        document.getElementById('totalHorses').textContent = data.total_horses;
        document.getElementById('totalRaces').textContent = data.total_races || 0;
        document.getElementById('totalWins').textContent = data.total_wins || 0;
        document.getElementById('totalPodiums').textContent = data.total_podiums || 0;
        
        const tbody = document.getElementById('horsesMasterBody');
        tbody.innerHTML = '';
        
        if (data.horses && data.horses.length > 0) {
            data.horses.forEach(horse => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td><strong>${horse.horse_name}</strong></td>
                    <td>${horse.jockey || '-'}</td>
                    <td>${horse.trainer || '-'}</td>
                    <td>${horse.total_races || 0}</td>
                    <td><strong>${horse.wins || 0}</strong></td>
                    <td><strong>${horse.podiums || 0}</strong></td>
                    <td>${horse.avg_position ? horse.avg_position.toFixed(2) : '-'}</td>
                `;
                tbody.appendChild(row);
            });
        }
        
        showStatus(`✅ ${data.total_horses} chevaux chargés!`, 'success');
    } catch (error) {
        showStatus(`Erreur: ${error.message}`, 'error');
    }
}

// Dashboard
async function loadDashboard() {
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard`);
        if (!response.ok) throw new Error('Erreur API');
        const data = await response.json();
        
        document.getElementById('dashHorses').textContent = data.total_unique_horses || 0;
        document.getElementById('dashRaces').textContent = data.total_races_tracked || 0;
        document.getElementById('dataQuality').textContent = getDataQuality(data.total_races_tracked);
        
        const recs = [];
        if (data.total_races_tracked < 20) recs.push('Importer au moins 20 courses');
        if (data.total_races_tracked < 50) recs.push('Continuer les imports pour améliorer le modèle');
        if (data.total_races_tracked < 100) recs.push('Atteindre 100 courses pour fiabilité');
        if (recs.length === 0) recs.push('Modèle bien alimenté! Utiliser pour prédictions');
        
        document.getElementById('recommendations').innerHTML = recs.map(r => `<li>${r}</li>`).join('');
    } catch (error) {
        console.error('Error:', error);
    }
}

// Utilities
function getConfidenceLevel(probability) {
    const barWidth = Math.round(probability * 100);
    let color = 'success';
    if (barWidth < 30) color = 'low';
    else if (barWidth < 50) color = 'medium';
    else color = 'high';
    
    return `<div class="confidence-bar ${color}" style="width: ${barWidth}%">${barWidth}%</div>`;
}

function getDataQuality(racesCount) {
    if (racesCount < 20) return 'Faible';
    if (racesCount < 50) return 'Acceptable';
    if (racesCount < 100) return 'Bonne';
    return 'Excellente';
}

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
