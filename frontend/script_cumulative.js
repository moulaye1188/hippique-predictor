// ============================================
// NEW: IMPORT DATA WITH CUMULATIVE SYSTEM
// ============================================

async function importFile() {
    const fileInput = document.getElementById('importFile');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Veuillez sélectionner un fichier');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    showStatus('Importation en cours...', 'loading');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/import`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            showStatus(`Erreur: ${data.error}`, 'error');
            return;
        }
        
        // Display results with new cumulative stats
        document.getElementById('importedCount').textContent = data.imported_races;
        document.getElementById('totalHorses').textContent = data.total_horses_in_system;
        document.getElementById('newHorses').textContent = data.new_horses_added;
        document.getElementById('updatedHorses').textContent = data.updated_horses;
        
        // Display preview
        const previewHtml = `
            <table class="results-table">
                <thead>
                    <tr>
                        ${data.columns.slice(0, 8).map(col => `<th>${col}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${data.preview.map(row => `
                        <tr>
                            ${data.columns.slice(0, 8).map(col => 
                                `<td>${row[col] || '-'}</td>`
                            ).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
        document.getElementById('importPreviewTable').innerHTML = previewHtml;
        document.getElementById('importResults').classList.remove('hidden');
        
        showStatus(`✅ ${data.imported_races} courses importées! ${data.total_horses_in_system} chevaux en BD.`, 'success');
        
        // Refresh horses list
        setTimeout(loadHorsesMaster, 500);
        
    } catch (error) {
        console.error('Error importing file:', error);
        showStatus(`Erreur: ${error.message}`, 'error');
    }
}

// ============================================
// NEW: LOAD MASTER HORSES WITH CUMULATIVE STATS
// ============================================

async function loadHorsesMaster() {
    showStatus('Chargement des chevaux...', 'loading');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/horses`);
        const data = await response.json();
        
        if (!response.ok) {
            showStatus(`Erreur: ${data.error}`, 'error');
            return;
        }
        
        // Calculate total stats
        const totalWins = data.horses.reduce((sum, h) => sum + (h.wins || 0), 0);
        const totalPodiums = data.horses.reduce((sum, h) => sum + (h.podiums || 0), 0);
        const totalRaces = data.horses.reduce((sum, h) => sum + (h.total_races || 0), 0);
        
        // Update stats display
        document.getElementById('totalHorsesMaster').textContent = data.total_horses;
        document.getElementById('totalRacesTracked').textContent = totalRaces;
        document.getElementById('totalWins').textContent = totalWins;
        document.getElementById('totalPodiums').textContent = totalPodiums;
        
        // Display horses table
        const horsesHtml = data.horses.map(horse => `
            <tr>
                <td><strong>${horse.horse_name}</strong></td>
                <td>${horse.jockey || '-'}</td>
                <td>${horse.trainer || '-'}</td>
                <td>${horse.total_races}</td>
                <td><strong>${horse.wins}</strong></td>
                <td><strong>${horse.podiums}</strong></td>
                <td>${horse.avg_position ? horse.avg_position.toFixed(2) : '-'}</td>
                <td>
                    <button class="btn btn-small" onclick="showHorseDetail(${horse.id})">Détail</button>
                </td>
            </tr>
        `).join('');
        
        document.getElementById('horsesMasterBody').innerHTML = horsesHtml || '<tr><td colspan="8">Aucun cheval en base de données</td></tr>';
        
        showStatus('✅ Chevaux chargés!', 'success');
        
    } catch (error) {
        console.error('Error loading horses:', error);
        showStatus(`Erreur: ${error.message}`, 'error');
    }
}

function showHorseDetail(horseId) {
    alert(`Détail du cheval #${horseId} (à implémenter)`);
}

// ============================================
// UPDATE DASHBOARD WITH CUMULATIVE DATA
// ============================================

async function loadDashboard() {
    showStatus('Chargement du dashboard...', 'loading');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/dashboard`);
        const data = await response.json();
        
        if (!response.ok) {
            showStatus(`Erreur: ${data.error}`, 'error');
            return;
        }
        
        // Update metrics with new fields
        document.getElementById('dashAccuracy').textContent = data.accuracy + '%';
        document.getElementById('dashTotal').textContent = data.total_predictions;
        document.getElementById('dashCorrect').textContent = data.correct_predictions;
        document.getElementById('dashHorses').textContent = data.total_unique_horses || 0;
        
        // Add races tracked if available
        if (data.total_races_tracked) {
            const racesCard = document.createElement('div');
            racesCard.className = 'metric-card';
            racesCard.innerHTML = `
                <h4>Courses Tracées</h4>
                <p class="metric-value">${data.total_races_tracked}</p>
            `;
            const metricsGrid = document.querySelector('.metrics-grid');
            if (metricsGrid && !metricsGrid.querySelector('[data-races]')) {
                racesCard.setAttribute('data-races', 'true');
                metricsGrid.appendChild(racesCard);
            }
        }
        
        // Draw accuracy timeline chart
        if (data.accuracy_timeline && data.accuracy_timeline.length > 0) {
            drawAccuracyChart(data.accuracy_timeline);
        }
        
        // Display recommendations
        const recsHtml = data.recommendations
            .map(rec => `<li>${rec}</li>`)
            .join('');
        document.getElementById('recommendations').innerHTML = recsHtml;
        
        // Display top factors
        const factorsHtml = data.top_factors
            .map(factor => `
                <tr>
                    <td>${factor.feature}</td>
                    <td>${factor.correlation}</td>
                    <td>${factor.strength}</td>
                </tr>
            `).join('');
        document.getElementById('topFactorsBody').innerHTML = factorsHtml || '<tr><td colspan="3">Pas de données</td></tr>';
        
        document.getElementById('dashboardMetrics').classList.remove('hidden');
        showStatus('✅ Dashboard chargé!', 'success');
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showStatus(`Erreur: ${error.message}`, 'error');
    }
}

// ============================================
// ADD HORSES TAB TO INITIALIZATION
// ============================================

function setupTabsCustom() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            
            // Remove active class from all buttons and contents
            tabButtons.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked button and corresponding content
            this.classList.add('active');
            document.getElementById(tabName).classList.add('active');
            
            // Load data for specific tabs
            if (tabName === 'horses') {
                loadHorsesMaster();
            } else if (tabName === 'dashboard') {
                loadDashboard();
            }
        });
    });
}

// Update initialization
document.addEventListener('DOMContentLoaded', function() {
    initializeHorses();
    setupTabsCustom();
    loadHistorique();
});
