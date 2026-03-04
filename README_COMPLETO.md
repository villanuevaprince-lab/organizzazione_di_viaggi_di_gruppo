# 🌍 SPA Viaggi di Gruppo - Verifica Informatica 2026

## 📋 Descrizione Progetto
**Single Page Application completa** per l'organizzazione di viaggi di gruppo tra amici, sviluppata per la verifica di informatica (3 ore).

### 🛠️ Stack Tecnologico
- **Frontend**: HTML5 + CSS3 + JavaScript Vanilla (NO framework)
- **Backend**: Flask 3.0 (Python)
- **Database**: MongoDB Atlas (cloud)
- **Librerie**: Leaflet.js (mappe), jsPDF (PDF), Flask-CORS, ReportLab

---

## 🚀 Avvio Rapido (GitHub Codespaces)

### 1. Installa Dipendenze Backend
```bash
cd backend
pip install -r requirements.txt
```

### 2. Avvia Backend (porta 8000)
```bash
cd backend
FLASK_APP=app.py FLASK_DEBUG=1 flask run --host 0.0.0.0 --port 8000
```

### 3. Avvia Frontend (porta 5500)
```bash
cd frontend
python3 -m http.server 5500
```

### 4. Accedi all'Applicazione
**Frontend**: https://<codespace>-5500.app.github.dev

**Credenziali di test**:
- `mario.rossi`
- `anna.verdi`
- `luca.bianchi`

---

## ✨ Funzionalità Implementate

### 🔐 A) Login (Priorità 1)
- ✅ Form username (NO password per semplicità)
- ✅ Verifica utente in database (creatore O partecipante)
- ✅ Sessioni Flask persistenti
- ✅ Redirect automatico alla dashboard

### 📋 B) Dashboard Viaggi
- ✅ Lista viaggi filtrata per utente loggato
- ✅ Card responsive con info principali
- ✅ Badge colorati stato (verde: futuro, rosso: concluso)
- ✅ Contatore viaggi dinamico
- ✅ Click su card → Dettaglio viaggio

### 🔍 C) Dettaglio Viaggio (Modal)
- ✅ Informazioni generali (destinazione, periodo, stato)
- ✅ **Tabella Partecipanti** con azioni
- ✅ **Tabella Attività** con azioni
- ✅ **Tabella Spese** con azioni
- ✅ **Riepilogo spese** (totale + per categoria)
- ✅ Badge stato viaggio

### ➕ D) Nuovo Viaggio
- ✅ Form completo con validazione
- ✅ Campi obbligatori: titolo, destinazione, data inizio
- ✅ Campi opzionali: data fine, note, coordinate GPS
- ✅ Creatore automatico = utente loggato
- ✅ Refresh automatico lista dopo creazione

### 👥 E) Gestione Partecipanti
- ✅ Aggiungi partecipante (username + nome)
- ✅ Rimuovi partecipante
- ✅ Tabella con ruolo e azioni
- ✅ Aggiornamento real-time dettaglio

### 🎯 F) Gestione Attività
- ✅ Aggiungi attività (titolo, tipo, descrizione, luogo)
- ✅ Rimuovi attività (con conferma)
- ✅ Tabella ordinata con tutte le info
- ✅ Tipo attività: visita, trasporto, pasto, altro

### 💰 G) Gestione Spese + Riepilogo
- ✅ Aggiungi spesa (descrizione, categoria, importo)
- ✅ Rimuovi spesa (con conferma)
- ✅ **Riepilogo automatico**:
  - Totale spese in EUR
  - Suddivisione per categoria
  - Badge colorati per ogni categoria
- ✅ Categorie: trasporto, alloggio, cibo, attività, shopping, varie

### 🗺️ H) Mappa Interattiva (Leaflet.js)
- ✅ Pagina dedicata accessibile da navigazione
- ✅ Marker colorati:
  - 🟢 Verde = Viaggio futuro
  - 🔴 Rosso = Viaggio concluso
- ✅ Popup marker con info + bottone dettagli
- ✅ Mappa OpenStreetMap
- ✅ Centrata su Italia

### 📄 I) Download PDF
- ✅ Generazione PDF backend (ReportLab)
- ✅ Contenuto PDF:
  - Informazioni generali viaggio
  - Lista partecipanti (max 10)
  - Lista attività (max 8)
  - Lista spese (max 10) + totale
  - Footer con data generazione
- ✅ Download automatico nel browser
- ✅ Nome file: `viaggio_<titolo>.pdf`

---

## 🏗️ Architettura Progetto

```
organizzazione_di_viaggi_di_gruppo/
├── backend/
│   ├── app.py              # Flask app con tutti gli endpoint
│   ├── requirements.txt    # Dipendenze Python
│   ├── .env                # MongoDB URI (già configurato)
│   └── README.md
├── frontend/
│   ├── index.html          # SPA (singola pagina)
│   ├── script.js           # Logica JavaScript completa
│   ├── style.css           # Stili responsive
│   └── README.md
└── README.md               # Questo file
```

---

## 🔌 API Backend (Flask)

### Autenticazione e Sessioni
```
POST   /api/login           # Login utente (crea sessione)
POST   /api/logout          # Logout utente
GET    /api/session         # Verifica sessione corrente
```

### Viaggi (richiede login)
```
GET    /api/viaggi          # Lista viaggi utente loggato
GET    /api/viaggi/:id      # Dettaglio singolo viaggio
POST   /api/viaggi          # Crea nuovo viaggio
PUT    /api/viaggi/:id      # Aggiorna viaggio (solo creatore)
```

### Partecipanti
```
POST   /api/viaggi/:id/partecipanti            # Aggiungi partecipante
DELETE /api/viaggi/:id/partecipanti/:username  # Rimuovi partecipante
```

### Attività
```
POST   /api/viaggi/:id/attivita         # Aggiungi attività
DELETE /api/viaggi/:id/attivita/:idx    # Rimuovi attività (indice)
```

### Spese
```
POST   /api/viaggi/:id/spese             # Aggiungi spesa
DELETE /api/viaggi/:id/spese/:idx        # Rimuovi spesa (indice)
GET    /api/viaggi/:id/spese/riepilogo   # Riepilogo totale + categorie
```

### Utilità
```
POST   /api/viaggi/:id/pdf    # Genera PDF viaggio
GET    /health                # Health check database
```

---

## 🗄️ Database MongoDB Atlas

### Connessione
```python
URI: mongodb+srv://Villanuevaprince_db:0oZfLe24uzcIZz9s@cluster0.rky3vjd.mongodb.net/
Database: organizzazione_viaggi
Collection: viaggi
```

### Struttura Documento Viaggio
```json
{
  "_id": ObjectId,
  "titolo": "Weekend a Berlino",
  "destinazione": "Berlino, Germania",
  "periodo": {
    "dataInizio": "2026-05-01",
    "dataFine": "2026-05-03"
  },
  "stato": "futuro",  // o "concluso"
  "location": {
    "lat": 52.52,
    "lng": 13.405
  },
  "creatore": {
    "id": "mario.rossi",
    "username": "mario.rossi",
    "nome": "Mario Rossi"
  },
  "partecipanti": [
    {
      "id": "anna.verdi",
      "username": "anna.verdi",
      "nome": "Anna Verdi",
      "ruolo": "partecipante"
    }
  ],
  "attivita": [
    {
      "titolo": "Museo Pergamon",
      "tipo": "visita",
      "descrizione": "Museo di antichità",
      "luogo": "Museo Pergamon",
      "dataOra": "2026-05-01T10:00:00Z",
      "durataMinuti": 120
    }
  ],
  "spese": [
    {
      "descrizione": "Volo A/R",
      "categoria": "trasporto",
      "importo": 250.00,
      "valuta": "EUR",
      "pagatore": {
        "username": "mario.rossi",
        "nome": "Mario Rossi"
      },
      "data": "2026-05-01",
      "note": null
    }
  ],
  "note": "Weekend culturale con amici.",
  "dataCreazione": "2026-01-10T10:00:00Z"
}
```

### Dati Esistenti
- ✅ **10 viaggi** già inseriti
- ✅ **3 utenti** presenti: mario.rossi, anna.verdi, luca.bianchi
- ✅ Viaggi con partecipanti, attività e spese complete

---

## 🎨 Frontend Caratteristiche

### 🖥️ Single Page Application (SPA)
- ✅ Singolo file HTML con routing via JavaScript
- ✅ Nessun reload di pagina
- ✅ Navigazione fluida tra viste
- ✅ Modal overlay per dettagli e form

### 📱 Design Responsive
- ✅ Mobile-first approach
- ✅ Card grid adattivo
- ✅ Tabelle scrollabili su mobile
- ✅ Bottoni touch-friendly

### 🎭 UX/UI Ottimizzata
- ✅ **Toast notifications** (success/error)
- ✅ **Loading spinners** durante chiamate API
- ✅ **Conferme** prima di eliminazioni
- ✅ **Validazione form** client-side
- ✅ **Badge colorati** per stati
- ✅ **Icone emoji** per migliore leggibilità
- ✅ **Animazioni** smooth per modal

### 🔧 Tecnologie Frontend
- ✅ **Fetch API** per chiamate HTTP
- ✅ **localStorage** per cache sessione (opzionale)
- ✅ **Leaflet.js 1.9.4** per mappe interattive
- ✅ **jsPDF 2.5.2** per generazione PDF client (nota: usato backend invece)
- ✅ **CSS Grid + Flexbox** per layout
- ✅ **CSS Custom Properties** per theming

---

## ⚙️ Configurazione CORS

Il backend è configurato per funzionare sia in **locale** che su **GitHub Codespaces**:

```python
# Auto-detection URL API nel frontend
function getApiBaseUrl() {
    const hostname = window.location.hostname;
    
    if (hostname.includes('app.github.dev')) {
        // Codespaces: sostituisci porta 5500 con 8000
        const backendHostname = hostname.replace(/-\d+\./, '-8000.');
        return `https://${backendHostname}`;
    }
    
    // Locale
    return 'http://localhost:8000';
}
```

---

## 🧪 Testing

### Test Endpoint Backend
```bash
# Health check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"mario.rossi"}'

# Lista viaggi (dopo login con cookie di sessione)
curl -X GET http://localhost:8000/api/viaggi --cookie-jar cookies.txt --cookie cookies.txt
```

### Test Frontend
1. Apri browser su `https://<codespace>-5500.app.github.dev`
2. Login con `mario.rossi`
3. Verifica:
   - Dashboard con 10 viaggi
   - Click su un viaggio → Modal con dettagli
   - Navigazione → Mappa con marker
   - Form nuovo viaggio funzionante
   - Aggiungi/rimuovi partecipanti, attività, spese
   - Download PDF

---

## 📝 Note Implementative

### Sessioni Flask
- ✅ Sessioni server-side con `session['username']`
- ✅ Cookie automatici (NO JWT per semplicità esame)
- ✅ Decorator `@login_required` su endpoint protetti
- ✅ Secret key configurabile via .env

### Error Handling
- ✅ Try-catch su tutte le API calls
- ✅ Messaggi errore user-friendly
- ✅ Logging errori backend
- ✅ Status code HTTP appropriati

### Validazioni
- ✅ **Client-side**: HTML5 required fields
- ✅ **Server-side**: controlli su campi obbligatori
- ✅ **Database**: ObjectId validation

### Sicurezza Esame
- ⚠️ NO password (login solo username per semplicità)
- ⚠️ CORS permissivo (`origins="*"`) per facilità testing
- ⚠️ Secret key hardcoded (OK per esame, NON produzione)

---

## 🎓 Valutazione Esame (Checklist)

### ✅ Requisiti Obbligatori
- [x] Login con sessione
- [x] Lista viaggi filtrata per utente
- [x] Dettaglio viaggio completo
- [x] Creazione nuovo viaggio
- [x] Gestione partecipanti (add/delete)
- [x] Gestione attività (add/delete)
- [x] Gestione spese + riepilogo
- [x] Mappa con Leaflet
- [x] Generazione PDF
- [x] Responsive mobile
- [x] Vanilla JavaScript (NO framework)
- [x] Flask backend
- [x] MongoDB Atlas connesso

### ⭐ Extra Punti
- [x] Toast notifications
- [x] Loading spinners
- [x] Conferme eliminazione
- [x] Validazione completa
- [x] Design moderno e pulito
- [x] Codice commentato
- [x] Auto-detection Codespaces
- [x] Error handling robusto

---

## 👨‍💻 Autore
**Sviluppato per**: Verifica Informatica 2026 (3 ore)  
**Tecnologie**: HTML/CSS/JS + Flask + MongoDB Atlas  
**Data**: Marzo 2026  
**Repository**: GitHub Codespaces

---

## 📚 Dipendenze

### Backend (`requirements.txt`)
```
Flask==3.0.0
Flask-CORS==4.0.0
pymongo==4.6.1
python-dotenv==1.0.0
reportlab==4.0.9
```

### Frontend (CDN)
- Leaflet.js 1.9.4
- jsPDF 2.5.2 (opzionale, PDF gestito backend)

---

## 🐛 Troubleshooting

### Problema: CORS Error
**Soluzione**: Verifica che backend sia in esecuzione e che CORS sia configurato con `origins="*"`

### Problema: Session non persiste
**Soluzione**: Verifica che `app.secret_key` sia configurata

### Problema: MongoDB non connesso
**Soluzione**: Verifica URI in `.env` e connessione internet

### Problema: PDF non scarica
**Soluzione**: Verifica che reportlab sia installato (`pip install reportlab`)

---

## 📞 Supporto
Per domande sull'esame, consulta il docente.  
Per bug tecnici, verifica i log Flask in console.

---

**🎉 Buon Esame!**
