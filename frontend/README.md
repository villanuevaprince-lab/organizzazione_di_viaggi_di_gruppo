# 🌐 Frontend SPA - Viaggi di Gruppo

Single Page Application (SPA) per organizzare viaggi di gruppo tra amici.

## 🛠️ Tecnologie

- **HTML5**: Struttura semantica
- **CSS3**: Styling moderno con variabili CSS, Grid, Flexbox
- **JavaScript Vanilla**: Logica applicativa (NO framework)

## 📁 Struttura

```
frontend/
├── index.html      # Struttura HTML
├── style.css       # Stili completi
├── script.js       # Logica JavaScript
└── README.md       # Questa documentazione
```

## ✨ Funzionalità

### 1. **Pagina Login**
- Input per username
- Validazione tramite API `/api/login`
- Utenti disponibili: `mario.rossi`, `anna.verdi`, `luca.bianchi`
- Gestione errori con messaggi chiari

### 2. **Dashboard Viaggi**
- Header con utente loggato e logout
- Griglia responsive di card viaggi
- Ogni card mostra:
  - Titolo viaggio
  - Destinazione
  - Date (inizio/fine)
  - Stato (badge colorato)
  - Numero partecipanti
- Loading state durante caricamento
- Empty state se non ci sono viaggi

### 3. **Modal Dettaglio Viaggio**
- Click su card → apre modal con dettagli completi
- Informazioni generali:
  - Destinazione, date, stato, organizzatore
  - Descrizione (se presente)
- Partecipanti con avatar e stato conferma
- Attività pianificate con date/orari
- Spese condivise con totale
- Chiusura con bottone X, click backdrop o tasto ESC

## 🎨 Design

### Caratteristiche
- **Responsive**: Si adatta a desktop, tablet, mobile
- **Tema moderno**: Colori Material Design inspired
- **Animazioni smooth**: Transizioni, hover effects, loading states
- **Accessibilità**: Focus states, contrasti leggibili

### Breakpoint
- Desktop: > 768px (griglia 3 colonne)
- Tablet: 768px (griglia 2 colonne)
- Mobile: < 480px (griglia 1 colonna)

### Stati
- **Pianificazione**: Badge giallo
- **Confermato**: Badge verde
- **Completato**: Badge blu
- **Annullato**: Badge rosso

## 🚀 Utilizzo

### Opzione 1: Aprire direttamente
```bash
cd frontend
# Apri index.html nel browser
open index.html  # macOS
xdg-open index.html  # Linux
start index.html  # Windows
```

### Opzione 2: Live Server (VS Code)
1. Installa estensione "Live Server"
2. Click destro su `index.html` → "Open with Live Server"
3. Si apre su `http://localhost:5500`

### Opzione 3: Python HTTP Server
```bash
cd frontend
python3 -m http.server 3000
# Apri http://localhost:3000
```

### Opzione 4: Node.js http-server
```bash
npm install -g http-server
cd frontend
http-server -p 3000
```

## 🔗 Configurazione API

Il file `script.js` contiene la configurazione API:

```javascript
const API_BASE_URL = 'http://localhost:8000';
```

**Modifica questa variabile** se il backend è su porta/host diverso.

## 📝 Workflow Utente

1. **Login**: Inserisci username → Verifica API
2. **Dashboard**: Visualizza lista viaggi dal database
3. **Dettaglio**: Click su viaggio → Modal con tutte le info
4. **Navigazione**: Chiudi modal, esplora altri viaggi
5. **Logout**: Torna alla schermata login

## 🔧 Personalizzazione

### Cambia colori
Modifica variabili CSS in `style.css`:
```css
:root {
    --primary-color: #2563eb;     /* Blu principale */
    --success-color: #10b981;      /* Verde */
    --danger-color: #ef4444;       /* Rosso */
    /* ... altre variabili ... */
}
```

### Cambia API endpoint
In `script.js`:
```javascript
const API_BASE_URL = 'https://tuodominio.com';
```

## 🐛 Troubleshooting

**Errore CORS**:
- Verifica che il backend abbia CORS abilitato
- Backend FastAPI ha già `CORSMiddleware` configurato

**API non risponde**:
- Verifica che backend sia avviato (`uvicorn app:app --reload`)
- Controlla console browser (F12) per errori rete
- Verifica `API_BASE_URL` in `script.js`

**Login fallisce**:
- Usa esattamente uno degli username esistenti
- Verifica MongoDB contenga viaggi con quell'utente

**Viaggi non compaiono**:
- Controlla console browser per errori API
- Verifica risposta API in Network tab (F12)
- Controlla che MongoDB Atlas sia accessibile

## 📱 Browser Support

- Chrome/Edge: ✅ (versioni recenti)
- Firefox: ✅ (versioni recenti)
- Safari: ✅ (versioni recenti)
- IE11: ❌ (non supportato)

## 🔐 Sicurezza

**NOTA**: Questa è una applicazione didattica con login semplificato:
- ❌ NO password
- ❌ NO token JWT
- ❌ NO sessioni persistenti
- ✅ Solo verifica username nel database

**Non usare in produzione senza implementare autenticazione completa.**

## 📊 Struttura Dati Attesa (API)

### Login Response
```json
{
  "success": true,
  "message": "Benvenuto mario.rossi!",
  "username": "mario.rossi"
}
```

### Viaggi Response
```json
{
  "success": true,
  "count": 10,
  "viaggi": [ /* array viaggio */ ]
}
```

### Viaggio Object
```json
{
  "_id": "string",
  "titolo": "string",
  "destinazione": "string",
  "data_inizio": "YYYY-MM-DD",
  "data_fine": "YYYY-MM-DD",
  "stato": "pianificazione|confermato|completato|annullato",
  "creatore": { "username": "...", "nome": "..." },
  "partecipanti": [ /* array */ ],
  "attivita": [ /* array */ ],
  "spese": [ /* array */ ]
}
```

## 🎓 Note Didattiche

Questo progetto dimostra:
- ✅ JavaScript moderno (ES6+)
- ✅ Fetch API per chiamate REST
- ✅ DOM manipulation
- ✅ Event handling
- ✅ Async/await patterns
- ✅ CSS Grid/Flexbox
- ✅ Responsive design
- ✅ Modal implementation
- ✅ State management (semplice)

**NO framework esterni** come richiesto (Angular/React/Vue).
