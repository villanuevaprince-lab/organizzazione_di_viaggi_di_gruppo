// ==============================================
// CONFIGURAZIONE API E STATO GLOBALE
// ==============================================

// Funzione per rilevare URL API in Codespaces o locale
function getApiBaseUrl() {
    const hostname = window.location.hostname;
    
    // Verifica se è Codespaces (formato: *.app.github.dev)
    if (hostname.includes('app.github.dev')) {
        // Sostituisci porta frontend (5500) con porta backend (8000)
        const backendHostname = hostname.replace(/-\d+\./, '-8000.');
        return `https://${backendHostname}`;
    }
    
    // Locale: backend su porta 8000
    return 'http://localhost:8000';
}

const API_BASE_URL = getApiBaseUrl();
console.log('API Base URL:', API_BASE_URL);

// Stato globale
let currentUser = null;
let viaggi = [];
let currentViaggioId = null;
let map = null;

// ==============================================
// UTILITY FUNCTIONS
// ==============================================

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT');
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

function showMessage(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function showError(element, message) {
    element.textContent = message;
    element.style.display = 'block';
}

function hideError(element) {
    element.style.display = 'none';
}

// ==============================================
// API CALLS CON SESSIONI
// ==============================================

async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            credentials: 'include', // Importante per sessioni
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || data.detail || 'Errore API');
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Verifica sessione
async function checkSession() {
    try {
        const data = await apiCall('/api/session');
        if (data.success && data.username) {
            currentUser = data.username;
            return true;
        }
        return false;
    } catch {
        return false;
    }
}

// Login
async function login(username, password) {
    return await apiCall('/api/login', {
        method: 'POST',
        body: JSON.stringify({ username, password })
    });
}

// Logout
async function logout() {
    return await apiCall('/api/logout', { method: 'POST' });
}

// Viaggi
async function getViaggi() {
    return await apiCall('/api/viaggi');
}

async function getViaggioDettaglio(id) {
    return await apiCall(`/api/viaggi/${id}`);
}

async function createViaggio(viaggioData) {
    return await apiCall('/api/viaggi', {
        method: 'POST',
        body: JSON.stringify(viaggioData)
    });
}

// Partecipanti
async function addPartecipante(viaggioId, partecipante) {
    return await apiCall(`/api/viaggi/${viaggioId}/partecipanti`, {
        method: 'POST',
        body: JSON.stringify(partecipante)
    });
}

async function removePartecipante(viaggioId, partId) {
    return await apiCall(`/api/viaggi/${viaggioId}/partecipanti/${partId}`, {
        method: 'DELETE'
    });
}

// Attività
async function addAttivita(viaggioId, attivita) {
    return await apiCall(`/api/viaggi/${viaggioId}/attivita`, {
        method: 'POST',
        body: JSON.stringify(attivita)
    });
}

async function removeAttivita(viaggioId, index) {
    return await apiCall(`/api/viaggi/${viaggioId}/attivita/${index}`, {
        method: 'DELETE'
    });
}

// Spese
async function addSpesa(viaggioId, spesa) {
    return await apiCall(`/api/viaggi/${viaggioId}/spese`, {
        method: 'POST',
        body: JSON.stringify(spesa)
    });
}

async function removeSpesa(viaggioId, index) {
    return await apiCall(`/api/viaggi/${viaggioId}/spese/${index}`, {
        method: 'DELETE'
    });
}

async function getRiepilogoSpese(viaggioId) {
    return await apiCall(`/api/viaggi/${viaggioId}/spese/riepilogo`);
}

// PDF
async function downloadPDF(viaggioId) {
    return await apiCall(`/api/viaggi/${viaggioId}/pdf`, {
        method: 'POST'
    });
}

// ==============================================
// UI - LOGIN
// ==============================================

function initLoginForm() {
    const loginForm = document.getElementById('login-form');
    if (!loginForm) {
        console.error('❌ Elemento login-form non trovato!');
        return;
    }
    
    loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('login-error');
    const submitBtn = e.target.querySelector('button[type="submit"]');
    
    hideError(errorDiv);
    submitBtn.disabled = true;
    submitBtn.querySelector('.btn-text').textContent = 'Accesso...';
    
    try {
        const result = await login(username, password);
        
        if (result.success) {
            currentUser = username;
            showLoginSuccess();
        }
    } catch (error) {
        showError(errorDiv, error.message);
        submitBtn.disabled = false;
        submitBtn.querySelector('.btn-text').textContent = 'Accedi';
    }
    });
}

function showLogin() {
    document.getElementById('login-container').classList.add('active');
    document.getElementById('app-container').classList.remove('active');
}

function showLoginSuccess() {
    document.getElementById('login-container').classList.remove('active');
    document.getElementById('app-container').classList.add('active');
    document.getElementById('logged-username').textContent = currentUser;
    
    // Carica viaggi
    loadViaggi();
}

function initLogoutButton() {
    const logoutBtn = document.getElementById('logout-btn');
    if (!logoutBtn) {
        console.error('❌ Elemento logout-btn non trovato!');
        return;
    }
    
    logoutBtn.addEventListener('click', async () => {
    try {
        await logout();
        currentUser = null;
        viaggi = [];
        showLogin();
        document.getElementById('username').value = '';
    } catch (error) {
        showMessage('Errore logout', 'error');
    }
    });
}

// ==============================================
// UI - NAVIGAZIONE
// ==============================================

function initNavigation() {
    document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const view = btn.dataset.view;
        switchView(view);
    });
    });
}

function switchView(viewName) {
    // Aggiorna nav attiva
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.querySelector(`[data-view="${viewName}"]`).classList.add('active');
    
    // Mostra vista
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById(`view-${viewName}`).classList.add('active');
    
    // Inizializza mappa se necessario
    if (viewName === 'mappa') {
        if (map) {
            map.remove();
            map = null;
        }
        initMap();
    }
}

// ==============================================
// UI - LISTA VIAGGI
// ==============================================

async function loadViaggi() {
    const loader = document.getElementById('viaggi-loader');
    const grid = document.getElementById('viaggi-grid');
    const noViaggi = document.getElementById('no-viaggi');
    const count = document.getElementById('viaggi-count');
    
    loader.style.display = 'flex';
    grid.innerHTML = '';
    noViaggi.style.display = 'none';
    
    try {
        const result = await getViaggi();
        viaggi = result.viaggi || [];
        
        loader.style.display = 'none';
        count.textContent = `${viaggi.length} viag${viaggi.length !== 1 ? 'gi' : 'gio'}`;
        
        if (viaggi.length === 0) {
            noViaggi.style.display = 'flex';
            grid.style.display = 'none';
        } else {
            grid.style.display = 'grid';
            renderViaggi();
        }
    } catch (error) {
        loader.style.display = 'none';
        showMessage('Errore caricamento viaggi', 'error');
    }
}

function renderViaggi() {
    const grid = document.getElementById('viaggi-grid');
    grid.innerHTML = '';
    
    viaggi.forEach(viaggio => {
        const card = document.createElement('div');
        card.className = 'viaggio-card';
        card.innerHTML = `
            <div class="card-header">
                <h3>${escapeHtml(viaggio.titolo) || 'Senza titolo'}</h3>
                <span class="badge ${viaggio.stato === 'futuro' ? 'badge-success' : 'badge-danger'}">
                    ${escapeHtml(viaggio.stato) || 'N/A'}
                </span>
            </div>
            <div class="card-body">
                <p><strong>📍</strong> ${escapeHtml(viaggio.destinazione) || 'N/A'}</p>
                <p><strong>📅</strong> ${formatDate(viaggio.periodo?.dataInizio)} 
                    ${viaggio.periodo?.dataFine ? '- ' + formatDate(viaggio.periodo.dataFine) : ''}</p>
                <p><strong>👥</strong> ${(viaggio.partecipanti?.length || 0) + 1} partecipanti</p>
                <p><strong>🎯</strong> ${viaggio.attivita?.length || 0} attività</p>
            </div>
            <div class="card-footer">
                <button class="btn btn-primary btn-small" onclick="openViaggioModal('${viaggio._id}')">
                    Dettagli
                </button>
            </div>
        `;
        grid.appendChild(card);
    });
}

// ==============================================
// UI - NUOVO VIAGGIO
// ==============================================

function initNewViaggioButton() {
    const newViaggioBtn = document.getElementById('new-viaggio-btn');
    if (!newViaggioBtn) return;
    
    newViaggioBtn.addEventListener('click', () => {
    document.getElementById('new-viaggio-modal').classList.add('active');
    });
}

function initNewViaggioModalButtons() {
    document.getElementById('close-new-viaggio-modal')?.addEventListener('click', closeNewViaggioModal);
    document.getElementById('cancel-new-viaggio')?.addEventListener('click', closeNewViaggioModal);
}

function closeNewViaggioModal() {
    document.getElementById('new-viaggio-modal').classList.remove('active');
    document.getElementById('new-viaggio-form').reset();
}

function initNewViaggioForm() {
    const form = document.getElementById('new-viaggio-form');
    if (!form) return;
    
    form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const viaggioData = {
        titolo: document.getElementById('nv-titolo').value.trim(),
        destinazione: document.getElementById('nv-destinazione').value.trim(),
        periodo: {
            dataInizio: document.getElementById('nv-data-inizio').value,
            dataFine: document.getElementById('nv-data-fine').value || null
        },
        stato: document.getElementById('nv-stato').value,
        descrizione: document.getElementById('nv-descrizione').value.trim() || null,
        note: document.getElementById('nv-note').value.trim() || null
    };
    
    const lat = document.getElementById('nv-lat').value;
    const lng = document.getElementById('nv-lng').value;
    if (lat && lng) {
        viaggioData.location = {
            lat: parseFloat(lat),
            lng: parseFloat(lng)
        };
    }
    
    try {
        const result = await createViaggio(viaggioData);
        
        if (result.success) {
            showMessage('Viaggio creato!');
            closeNewViaggioModal();
            await loadViaggi();
        }
    } catch (error) {
        showMessage(error.message, 'error');
    }
    });
}

// ==============================================
// UI - DETTAGLIO VIAGGIO
// ==============================================

async function openViaggioModal(viaggioId) {
    currentViaggioId = viaggioId;
    const modal = document.getElementById('viaggio-modal');
    const loader = document.getElementById('modal-loader');
    const details = document.getElementById('modal-details');
    
    modal.classList.add('active');
    loader.style.display = 'flex';
    details.style.display = 'none';
    
    try {
        const result = await getViaggioDettaglio(viaggioId);
        const viaggio = result.viaggio;
        
        loader.style.display = 'none';
        details.style.display = 'block';
        
        renderViaggioDetails(viaggio);
    } catch (error) {
        loader.style.display = 'none';
        showMessage('Errore caricamento dettagli', 'error');
    }
}

function renderViaggioDetails(viaggio) {
    // Titolo
    document.getElementById('modal-title').textContent = viaggio.titolo || 'Viaggio';
    
    // Info generali
    const infoDiv = document.getElementById('viaggio-info');
    infoDiv.innerHTML = `
        <div class="info-grid">
            <div><strong>Destinazione:</strong> ${escapeHtml(viaggio.destinazione) || 'N/A'}</div>
            <div><strong>Stato:</strong> <span class="badge ${viaggio.stato === 'futuro' ? 'badge-success' : 'badge-danger'}">${escapeHtml(viaggio.stato)}</span></div>
            <div><strong>Data Inizio:</strong> ${formatDate(viaggio.periodo?.dataInizio)}</div>
            <div><strong>Data Fine:</strong> ${formatDate(viaggio.periodo?.dataFine)}</div>
            <div><strong>Creatore:</strong> ${escapeHtml(viaggio.creatore?.nome || viaggio.creatore?.username) || 'N/A'}</div>
            ${viaggio.descrizione ? `<div><strong>Descrizione:</strong> ${escapeHtml(viaggio.descrizione)}</div>` : ''}
            ${viaggio.note ? `<div><strong>Note:</strong> ${escapeHtml(viaggio.note)}</div>` : ''}
        </div>
    `;
    
    // Partecipanti
    renderPartecipanti(viaggio.partecipanti || []);
    
    // Attività
    renderAttivita(viaggio.attivita || []);
    
    // Spese
    renderSpese(viaggio.spese || []);
    loadRiepilogoSpese();
}

function renderPartecipanti(partecipanti) {
    const list = document.getElementById('partecipanti-list');
    document.getElementById('part-count').textContent = `(${partecipanti.length})`;
    
    if (partecipanti.length === 0) {
        list.innerHTML = '<p class="empty-text">Nessun partecipante</p>';
        return;
    }
    
    list.innerHTML = `
        <table class="data-table">
            <thead>
                <tr>
                    <th>Nome</th>
                    <th>ID</th>
                    <th>Note</th>
                    <th>Azioni</th>
                </tr>
            </thead>
            <tbody>
                ${partecipanti.map((p, idx) => `
                    <tr>
                        <td>${escapeHtml(p.nome) || 'N/A'}</td>
                        <td>${escapeHtml(p.id) || 'N/A'}</td>
                        <td>${escapeHtml(p.note) || '-'}</td>
                        <td>
                            <button class="btn-icon" onclick="deletePartecipante('${escapeHtml(p.id)}')", title="Rimuovi">
                                🗑️
                            </button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

function renderAttivita(attivita) {
    const list = document.getElementById('attivita-list');
    document.getElementById('att-count').textContent = `(${attivita.length})`;
    
    if (attivita.length === 0) {
        list.innerHTML = '<p class="empty-text">Nessuna attività</p>';
        return;
    }
    
    list.innerHTML = `
        <table class="data-table">
            <thead>
                <tr>
                    <th>Titolo</th>
                    <th>Tipo</th>
                    <th>Luogo</th>
                    <th>Azioni</th>
                </tr>
            </thead>
            <tbody>
                ${attivita.map((a, idx) => `
                    <tr>
                        <td>
                            <strong>${a.titolo || 'N/A'}</strong>
                            ${a.descrizione ? `<br><small>${a.descrizione}</small>` : ''}
                        </td>
                        <td>${a.tipo || 'N/A'}</td>
                        <td>${a.luogo || 'N/A'}</td>
                        <td>
                            <button class="btn-icon" onclick="deleteAttivita(${idx})" title="Rimuovi">
                                🗑️
                            </button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

function renderSpese(spese) {
    const list = document.getElementById('spese-list');
    document.getElementById('spese-count').textContent = `(${spese.length})`;
    
    if (spese.length === 0) {
        list.innerHTML = '<p class="empty-text">Nessuna spesa</p>';
        return;
    }
    
    list.innerHTML = `
        <table class="data-table">
            <thead>
                <tr>
                    <th>Descrizione</th>
                    <th>Categoria</th>
                    <th>Importo</th>
                    <th>Azioni</th>
                </tr>
            </thead>
            <tbody>
                ${spese.map((s, idx) => `
                    <tr>
                        <td>${s.descrizione || 'N/A'}</td>
                        <td>${s.categoria || 'varie'}</td>
                        <td><strong>${s.importo?.toFixed(2) || '0.00'} ${s.valuta || 'EUR'}</strong></td>
                        <td>
                            <button class="btn-icon" onclick="deleteSpesa(${idx})" title="Rimuovi">
                                🗑️
                            </button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

async function loadRiepilogoSpese() {
    try {
        const result = await getRiepilogoSpese(currentViaggioId);
        const riepilogo = document.getElementById('riepilogo-spese');
        
        const categorie = Object.entries(result.perCategoria || {})
            .map(([cat, tot]) => `<span class="badge">${cat}: ${tot.toFixed(2)} €</span>`)
            .join(' ');
        
        riepilogo.innerHTML = `
            <div class="riepilogo-box">
                <h4>Riepilogo Totale</h4>
                <p class="total-amount">${result.totale?.toFixed(2) || '0.00'} ${result.valuta || 'EUR'}</p>
                <div class="categories">${categorie || '<span class="empty-text">Nessuna spesa</span>'}</div>
            </div>
        `;
    } catch (error) {
        console.error('Errore riepilogo:', error);
    }
}

function initViaggioModalButtons() {
    const closeBtn = document.getElementById('close-viaggio-modal');
    if (!closeBtn) return;
    
    closeBtn.addEventListener('click', () => {
        document.getElementById('viaggio-modal').classList.remove('active');
    });
}

// ==============================================
// UI - GESTIONE PARTECIPANTI
// ==============================================

function initPartecipantiButtons() {
    document.getElementById('add-partecipante-btn')?.addEventListener('click', () => {
    document.getElementById('add-partecipante-modal').classList.add('active');
    });
    
    document.getElementById('close-add-partecipante')?.addEventListener('click', closeAddPartecipanteModal);
    document.getElementById('cancel-add-partecipante')?.addEventListener('click', closeAddPartecipanteModal);
}

function closeAddPartecipanteModal() {
    document.getElementById('add-partecipante-modal').classList.remove('active');
    document.getElementById('add-partecipante-form').reset();
}

function initPartecipantiForm() {
    const form = document.getElementById('add-partecipante-form');
    if (!form) return;
    
    form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const partecipante = {
        id: document.getElementById('ap-id').value.trim(),
        nome: document.getElementById('ap-nome').value.trim(),
        note: document.getElementById('ap-note').value.trim() || null
    };
    
    try {
        const result = await addPartecipante(currentViaggioId, partecipante);
        
        if (result.success) {
            showMessage('Partecipante aggiunto!');
            closeAddPartecipanteModal();
            // Ricarica dettagli
            openViaggioModal(currentViaggioId);
        }
    } catch (error) {
        showMessage(error.message, 'error');
    }
    });
}

async function deletePartecipante(partId) {
    if (!confirm(`Rimuovere ${partId}?`)) return;
    
    try {
        const result = await removePartecipante(currentViaggioId, partId);
        
        if (result.success) {
            showMessage('Partecipante rimosso!');
            openViaggioModal(currentViaggioId);
        }
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

// ==============================================
// UI - GESTIONE ATTIVITÀ
// ==============================================

function initAttivitaButtons() {
    document.getElementById('add-attivita-btn')?.addEventListener('click', () => {
    document.getElementById('add-attivita-modal').classList.add('active');
    });
    
    document.getElementById('close-add-attivita')?.addEventListener('click', closeAddAttivitaModal);
    document.getElementById('cancel-add-attivita')?.addEventListener('click', closeAddAttivitaModal);
}

function closeAddAttivitaModal() {
    document.getElementById('add-attivita-modal').classList.remove('active');
    document.getElementById('add-attivita-form').reset();
}

function initAttivitaForm() {
    const form = document.getElementById('add-attivita-form');
    if (!form) return;
    
    form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const attivita = {
        titolo: document.getElementById('aa-titolo').value.trim(),
        tipo: document.getElementById('aa-tipo').value,
        descrizione: document.getElementById('aa-descrizione').value.trim(),
        luogo: document.getElementById('aa-luogo').value.trim()
    };
    
    try {
        const result = await addAttivita(currentViaggioId, attivita);
        
        if (result.success) {
            showMessage('Attività aggiunta!');
            closeAddAttivitaModal();
            openViaggioModal(currentViaggioId);
        }
    } catch (error) {
        showMessage(error.message, 'error');
    }
    });
}

async function deleteAttivita(index) {
    if (!confirm('Rimuovere questa attività?')) return;
    
    try {
        const result = await removeAttivita(currentViaggioId, index);
        
        if (result.success) {
            showMessage('Attività rimossa!');
            openViaggioModal(currentViaggioId);
        }
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

// ==============================================
// UI - GESTIONE SPESE
// ==============================================

function initSpeseButtons() {
    document.getElementById('add-spesa-btn')?.addEventListener('click', () => {
    document.getElementById('add-spesa-modal').classList.add('active');
    });
    
    document.getElementById('close-add-spesa')?.addEventListener('click', closeAddSpesaModal);
    document.getElementById('cancel-add-spesa')?.addEventListener('click', closeAddSpesaModal);
}

function closeAddSpesaModal() {
    document.getElementById('add-spesa-modal').classList.remove('active');
    document.getElementById('add-spesa-form').reset();
}

function initSpeseForm() {
    const form = document.getElementById('add-spesa-form');
    if (!form) return;
    
    form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const spesa = {
        descrizione: document.getElementById('as-descrizione').value.trim(),
        categoria: document.getElementById('as-categoria').value,
        importo: parseFloat(document.getElementById('as-importo').value)
    };
    
    try {
        const result = await addSpesa(currentViaggioId, spesa);
        
        if (result.success) {
            showMessage('Spesa aggiunta!');
            closeAddSpesaModal();
            openViaggioModal(currentViaggioId);
        }
    } catch (error) {
        showMessage(error.message, 'error');
    }
    });
}

async function deleteSpesa(index) {
    if (!confirm('Rimuovere questa spesa?')) return;
    
    try {
        const result = await removeSpesa(currentViaggioId, index);
        
        if (result.success) {
            showMessage('Spesa rimossa!');
            openViaggioModal(currentViaggioId);
        }
    } catch (error) {
        showMessage(error.message, 'error');
    }
}

// ==============================================
// UI - MAPPA LEAFLET
// ==============================================

function initMap() {
    if (map) return; // Già inizializzata
    
    const container = document.getElementById('map-container');
    map = L.map(container).setView([45.4642, 9.1900], 5); // Centra su Italia
    
    // Tile layer OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    // Aggiungi marker per tutti i viaggi con location
    viaggi.forEach(viaggio => {
        if (viaggio.location && viaggio.location.lat && viaggio.location.lng) {
            const iconColor = viaggio.stato === 'futuro' ? 'green' : 'red';
            const icon = L.divIcon({
                className: 'custom-marker',
                html: `<div style="background-color: ${iconColor}; width: 25px; height: 25px; border-radius: 50%; border: 2px solid white;"></div>`,
                iconSize: [25, 25]
            });
            
            const marker = L.marker([viaggio.location.lat, viaggio.location.lng], { icon })
                .addTo(map);
            
            const popupContent = `
                <div style="min-width: 150px;">
                    <h4 style="margin: 0 0 8px 0;">${viaggio.titolo}</h4>
                    <p style="margin: 0; font-size: 13px;">${viaggio.destinazione}</p>
                    <p style="margin: 4px 0 0 0; font-size: 12px; color: #666;">
                        ${formatDate(viaggio.periodo?.dataInizio)}
                    </p>
                    <button onclick="openViaggioModal('${viaggio._id}')" 
                            style="margin-top: 8px; padding: 4px 8px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        Dettagli
                    </button>
                </div>
            `;
            
            marker.bindPopup(popupContent);
        }
    });
    
    // Ridimensiona mappa dopo init
    setTimeout(() => map.invalidateSize(), 200);
}

// ==============================================
// UI - DOWNLOAD PDF
// ==============================================

function initPdfButton() {
    const pdfBtn = document.getElementById('download-pdf-btn');
    if (!pdfBtn) return;
    
    pdfBtn.addEventListener('click', async () => {
    try {
        const result = await downloadPDF(currentViaggioId);
        
        if (result.success && result.pdf) {
            // Decodifica base64 e scarica
            const pdfData = atob(result.pdf);
            const bytes = new Uint8Array(pdfData.length);
            for (let i = 0; i < pdfData.length; i++) {
                bytes[i] = pdfData.charCodeAt(i);
            }
            
            const blob = new Blob([bytes], { type: 'application/pdf' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = result.filename || 'viaggio.pdf';
            a.click();
            URL.revokeObjectURL(url);
            
            showMessage('PDF generato!');
        }
    } catch (error) {
        showMessage('Errore generazione PDF', 'error');
    }
    });
}

// ==============================================
// INIT APP
// ==============================================

async function init() {
    console.log('🚀 Inizializzazione SPA Viaggi di Gruppo');
    console.log('📡 API URL:', API_BASE_URL);
    
    // 1. Inizializza tutti gli event listeners dopo che il DOM è pronto
    initLoginForm();
    initLogoutButton();
    initNavigation();
    initNewViaggioButton();
    initNewViaggioModalButtons();
    initNewViaggioForm();
    initViaggioModalButtons();
    initPartecipantiButtons();
    initPartecipantiForm();
    initAttivitaButtons();
    initAttivitaForm();
    initSpeseButtons();
    initSpeseForm();
    initPdfButton();
    
    console.log('✅ Event listeners inizializzati');
    
    // 2. Verifica se c'è una sessione attiva
    try {
        const hasSession = await checkSession();
        
        if (hasSession) {
            console.log('✅ Sessione attiva trovata:', currentUser);
            showLoginSuccess();
        } else {
            console.log('ℹ️ Nessuna sessione attiva, mostra login');
            showLogin();
        }
    } catch (error) {
        console.error('❌ Errore verifica sessione:', error);
        showLogin();
    }
}

// Avvia app quando DOM è completamente caricato
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    // DOM già caricato
    init();
}
