// ===== CONFIGURAZIONE =====
// Rileva automaticamente l'URL del backend in base all'ambiente
function getApiBaseUrl() {
    const hostname = window.location.hostname;
    
    // Se siamo in GitHub Codespaces o ambiente simile
    if (hostname.includes('github.dev') || 
        hostname.includes('githubpreview.dev') ||
        hostname.includes('app.github.dev') ||
        hostname.includes('preview.app.github.dev')) {
        
        // Pattern: nome-codespace-PORTA.dominio
        // Sostituisci la porta corrente con 8000 (porta backend)
        const backendHostname = hostname.replace(/-\d+\./, '-8000.');
        return `${window.location.protocol}//${backendHostname}`;
    }
    
    // Sviluppo locale
    return 'http://localhost:8000';
}

const API_BASE_URL = getApiBaseUrl();
console.log('🌐 Ambiente rilevato:', window.location.hostname);
console.log('🔗 API Base URL:', API_BASE_URL);

// ===== STATO APPLICAZIONE =====
let currentUser = null;
let viaggi = [];
let currentViaggioId = null;

// ===== ELEMENTI DOM =====
const elements = {
    // Login
    loginContainer: document.getElementById('login-container'),
    appContainer: document.getElementById('app-container'),
    loginForm: document.getElementById('login-form'),
    usernameInput: document.getElementById('username'),
    loginError: document.getElementById('login-error'),
    
    // Header
    loggedUsername: document.getElementById('logged-username'),
    logoutBtn: document.getElementById('logout-btn'),
    
    // Viaggi
    viaggiLoader: document.getElementById('viaggi-loader'),
    viaggiGrid: document.getElementById('viaggi-grid'),
    noViaggi: document.getElementById('no-viaggi'),
    viaggiCount: document.getElementById('viaggi-count'),
    
    // Modal
    viaggioModal: document.getElementById('viaggio-modal'),
    modalTitle: document.getElementById('modal-title'),
    modalLoader: document.getElementById('modal-loader'),
    modalDetails: document.getElementById('modal-details'),
    closeModal: document.getElementById('close-modal')
};

// ===== UTILITÀ =====
function formatDate(dateString) {
    if (!dateString) return 'N/D';
    const date = new Date(dateString);
    return date.toLocaleDateString('it-IT', { year: 'numeric', month: 'long', day: 'numeric' });
}

function getInitials(name) {
    if (!name) return '?';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
}

function showError(element, message) {
    element.textContent = message;
    element.classList.add('show');
    setTimeout(() => element.classList.remove('show'), 5000);
}

function setLoading(button, isLoading) {
    if (isLoading) {
        button.disabled = true;
        button.classList.add('loading');
    } else {
        button.disabled = false;
        button.classList.remove('loading');
    }
}

// ===== API CALLS =====
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Errore nella richiesta');
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

async function login(username) {
    return await apiCall('/api/login', {
        method: 'POST',
        body: JSON.stringify({ username })
    });
}

async function getViaggi() {
    return await apiCall('/api/viaggi');
}

async function getViaggioDettaglio(viaggioId) {
    return await apiCall(`/api/viaggi/${viaggioId}`);
}

// ===== LOGIN =====
elements.loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = elements.usernameInput.value.trim();
    const submitBtn = elements.loginForm.querySelector('button[type="submit"]');
    
    elements.loginError.classList.remove('show');
    setLoading(submitBtn, true);
    
    try {
        const response = await login(username);
        
        if (response.success) {
            currentUser = response.username;
            showApp();
            await loadViaggi();
        }
    } catch (error) {
        showError(elements.loginError, error.message || 'Errore durante il login');
    } finally {
        setLoading(submitBtn, false);
    }
});

// ===== LOGOUT =====
elements.logoutBtn.addEventListener('click', () => {
    currentUser = null;
    viaggi = [];
    elements.usernameInput.value = '';
    elements.loginContainer.classList.add('active');
    elements.appContainer.classList.remove('active');
    closeModalViaggio();
});

// ===== MOSTRA APP =====
function showApp() {
    elements.loginContainer.classList.remove('active');
    elements.appContainer.classList.add('active');
    elements.loggedUsername.textContent = currentUser;
}

// ===== CARICA VIAGGI =====
async function loadViaggi() {
    elements.viaggiLoader.style.display = 'block';
    elements.viaggiGrid.classList.remove('active');
    elements.noViaggi.classList.remove('active');
    
    try {
        const response = await getViaggi();
        
        if (response.success) {
            viaggi = response.viaggi;
            elements.viaggiCount.textContent = `${response.count} ${response.count === 1 ? 'viaggio' : 'viaggi'}`;
            
            if (viaggi.length > 0) {
                renderViaggi();
            } else {
                elements.noViaggi.classList.add('active');
            }
        }
    } catch (error) {
        console.error('Errore caricamento viaggi:', error);
        elements.noViaggi.classList.add('active');
        showError(elements.loginError, 'Errore nel caricamento dei viaggi');
    } finally {
        elements.viaggiLoader.style.display = 'none';
    }
}

// ===== RENDER VIAGGI =====
function renderViaggi() {
    elements.viaggiGrid.innerHTML = '';
    
    viaggi.forEach(viaggio => {
        const card = createViaggioCard(viaggio);
        elements.viaggiGrid.appendChild(card);
    });
    
    elements.viaggiGrid.classList.add('active');
}

function createViaggioCard(viaggio) {
    const card = document.createElement('div');
    card.className = 'viaggio-card';
    card.onclick = () => openViaggioModal(viaggio._id);
    
    const partecipantiCount = viaggio.partecipanti ? viaggio.partecipanti.length : 0;
    const stato = viaggio.stato || 'pianificazione';
    const statoClass = `status-${stato.toLowerCase()}`;
    
    card.innerHTML = `
        <div class="viaggio-card-header">
            <h3>${viaggio.titolo || 'Viaggio senza titolo'}</h3>
            <div class="viaggio-destination">
                📍 ${viaggio.destinazione || 'Destinazione non specificata'}
            </div>
            ${viaggio.data_inizio ? `
                <div class="viaggio-date">
                    📅 ${formatDate(viaggio.data_inizio)}${viaggio.data_fine ? ` - ${formatDate(viaggio.data_fine)}` : ''}
                </div>
            ` : ''}
        </div>
        <div class="viaggio-card-footer">
            <span class="status-badge ${statoClass}">
                ${stato.charAt(0).toUpperCase() + stato.slice(1)}
            </span>
            <span class="partecipanti-count">
                👥 ${partecipantiCount} ${partecipantiCount === 1 ? 'persona' : 'persone'}
            </span>
        </div>
    `;
    
    return card;
}

// ===== MODAL DETTAGLIO =====
async function openViaggioModal(viaggioId) {
    currentViaggioId = viaggioId;
    elements.viaggioModal.classList.add('active');
    elements.modalLoader.style.display = 'block';
    elements.modalDetails.classList.remove('active');
    document.body.style.overflow = 'hidden';
    
    try {
        const response = await getViaggioDettaglio(viaggioId);
        
        if (response.success) {
            renderViaggioDettaglio(response.viaggio);
        }
    } catch (error) {
        console.error('Errore caricamento dettaglio:', error);
        elements.modalDetails.innerHTML = `
            <div class="empty-state active">
                <div class="empty-icon">⚠️</div>
                <h3>Errore</h3>
                <p>Impossibile caricare i dettagli del viaggio</p>
            </div>
        `;
        elements.modalDetails.classList.add('active');
    } finally {
        elements.modalLoader.style.display = 'none';
    }
}

function closeModalViaggio() {
    elements.viaggioModal.classList.remove('active');
    currentViaggioId = null;
    document.body.style.overflow = '';
}

elements.closeModal.addEventListener('click', closeModalViaggio);
elements.viaggioModal.querySelector('.modal-backdrop').addEventListener('click', closeModalViaggio);

// Chiudi modal con ESC
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && elements.viaggioModal.classList.contains('active')) {
        closeModalViaggio();
    }
});

// ===== RENDER DETTAGLIO VIAGGIO =====
function renderViaggioDettaglio(viaggio) {
    elements.modalTitle.textContent = viaggio.titolo || 'Viaggio senza titolo';
    
    let html = '<div class="detail-section">';
    
    // Informazioni principali
    html += '<h3>📋 Informazioni Generali</h3>';
    html += '<div class="detail-info">';
    html += `<div class="info-row">
        <span class="info-label">Destinazione:</span>
        <span class="info-value">${viaggio.destinazione || 'Non specificata'}</span>
    </div>`;
    
    if (viaggio.data_inizio) {
        html += `<div class="info-row">
            <span class="info-label">Date:</span>
            <span class="info-value">${formatDate(viaggio.data_inizio)} ${viaggio.data_fine ? `- ${formatDate(viaggio.data_fine)}` : ''}</span>
        </div>`;
    }
    
    html += `<div class="info-row">
        <span class="info-label">Stato:</span>
        <span class="info-value">
            <span class="status-badge status-${(viaggio.stato || 'pianificazione').toLowerCase()}">
                ${(viaggio.stato || 'pianificazione').charAt(0).toUpperCase() + (viaggio.stato || 'pianificazione').slice(1)}
            </span>
        </span>
    </div>`;
    
    if (viaggio.descrizione) {
        html += `<div class="info-row">
            <span class="info-label">Descrizione:</span>
            <span class="info-value">${viaggio.descrizione}</span>
        </div>`;
    }
    
    if (viaggio.creatore) {
        html += `<div class="info-row">
            <span class="info-label">Organizzatore:</span>
            <span class="info-value">${viaggio.creatore.nome || viaggio.creatore.username}</span>
        </div>`;
    }
    
    html += '</div></div>';
    
    // Partecipanti
    if (viaggio.partecipanti && viaggio.partecipanti.length > 0) {
        html += '<div class="detail-section">';
        html += '<h3>👥 Partecipanti</h3>';
        html += '<div class="partecipanti-list">';
        
        viaggio.partecipanti.forEach(p => {
            const confermato = p.confermato ? '✅ Confermato' : '⏳ In attesa';
            html += `
                <div class="partecipante-item">
                    <div class="partecipante-avatar">${getInitials(p.nome || p.username)}</div>
                    <div class="partecipante-info">
                        <div class="partecipante-nome">${p.nome || p.username}</div>
                        <div class="partecipante-status">${confermato}</div>
                    </div>
                </div>
            `;
        });
        
        html += '</div></div>';
    }
    
    // Attività
    if (viaggio.attivita && viaggio.attivita.length > 0) {
        html += '<div class="detail-section">';
        html += '<h3>🎯 Attività Pianificate</h3>';
        html += '<div class="attivita-list">';
        
        viaggio.attivita.forEach(att => {
            html += `
                <div class="attivita-item">
                    <div class="attivita-title">${att.titolo}</div>
                    ${att.descrizione ? `<div class="info-value">${att.descrizione}</div>` : ''}
                    <div class="attivita-meta">
                        ${att.data ? `<span>📅 ${formatDate(att.data)}</span>` : ''}
                        ${att.orario ? `<span>🕐 ${att.orario}</span>` : ''}
                    </div>
                </div>
            `;
        });
        
        html += '</div></div>';
    }
    
    // Spese
    if (viaggio.spese && viaggio.spese.length > 0) {
        html += '<div class="detail-section">';
        html += '<h3>💰 Spese Condivise</h3>';
        html += '<div class="spese-list">';
        
        let totale = 0;
        viaggio.spese.forEach(spesa => {
            totale += spesa.importo || 0;
            const divisaCount = spesa.divisa_tra ? spesa.divisa_tra.length : 0;
            
            html += `
                <div class="spesa-item">
                    <div class="spesa-description">${spesa.descrizione}</div>
                    <div class="spesa-amount">${spesa.importo?.toFixed(2) || '0.00'} ${spesa.valuta || 'EUR'}</div>
                    <div class="spesa-meta">
                        ${spesa.pagato_da ? `<span>💳 Pagato da: ${spesa.pagato_da}</span>` : ''}
                        ${divisaCount > 0 ? `<span>👥 Divisa tra ${divisaCount} ${divisaCount === 1 ? 'persona' : 'persone'}</span>` : ''}
                    </div>
                </div>
            `;
        });
        
        html += `</div>`;
        html += `<div style="margin-top: 1rem; padding-top: 1rem; border-top: 2px solid var(--border-color); text-align: right;">
            <strong style="font-size: 1.25rem;">Totale: ${totale.toFixed(2)} EUR</strong>
        </div>`;
        html += '</div>';
    }
    
    // Se non ci sono attività né spese
    if ((!viaggio.attivita || viaggio.attivita.length === 0) && 
        (!viaggio.spese || viaggio.spese.length === 0)) {
        html += `
            <div class="empty-state active">
                <div class="empty-icon">📝</div>
                <h3>Nessun dettaglio aggiuntivo</h3>
                <p>Non ci sono attività o spese pianificate per questo viaggio</p>
            </div>
        `;
    }
    
    elements.modalDetails.innerHTML = html;
    elements.modalDetails.classList.add('active');
}

// ===== INIZIALIZZAZIONE =====
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 SPA Viaggi di Gruppo caricata');
    console.log('API Base URL:', API_BASE_URL);
    
    // Focus su input username
    elements.usernameInput.focus();
});
