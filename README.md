# ✈️ SPA Viaggi di Gruppo

**Single Page Application** per organizzare viaggi di gruppo tra amici.

Progetto sviluppato per esercizio informatica: backend REST API + frontend vanilla JavaScript.

---

## 🎯 Caratteristiche Principali

- **Backend**: Flask con MongoDB Atlas
- **Frontend**: HTML/CSS/JavaScript puro (NO framework)
- **Database**: MongoDB Atlas (già popolato con 10 viaggi)
- **Funzionalità**: Login utente, elenco viaggi, dettaglio completo
- **Design**: Responsive, moderno, animazioni smooth

---

## 📁 Struttura Progetto

```
spa-viaggi/
├── backend/                    # API REST Flask
│   ├── app.py                 # Applicazione principale
│   ├── requirements.txt       # Dipendenze Python
│   ├── .env                   # Configurazione MongoDB
│   └── README.md              # Documentazione backend
│
├── frontend/                   # Single Page Application
│   ├── index.html             # Struttura HTML
│   ├── style.css              # Stili CSS
│   ├── script.js              # Logica JavaScript
│   └── README.md              # Documentazione frontend
│
├── .gitignore
└── README.md                   # Questo file
```

---

## 🚀 Quick Start

### 1️⃣ Backend (API REST)

```bash
# Vai nella cartella backend
cd backend

# Installa dipendenze
pip install -r requirements.txt

# Avvia il server
flask run --host 0.0.0.0 --port 8000 --debug
```

✅ **Backend attivo su**: http://localhost:8000

### 2️⃣ Frontend (SPA)

```bash
# Vai nella cartella frontend
cd frontend

# Apri index.html nel browser o usa live server
# Opzione 1: Doppio click su index.html
# Opzione 2: Python server
python3 -m http.server 3000
```

✅ **Frontend attivo su**: http://localhost:3000

---

## 🔌 API Endpoints

### **POST** `/api/login`
Login utente (verifica username esistente nei viaggi)

**Body**:
```json
{
  "username": "mario.rossi"
}
```

**Utenti disponibili**: `mario.rossi`, `anna.verdi`, `luca.bianchi`

---

### **GET** `/api/viaggi`
Restituisce l'elenco di tutti i viaggi

**Response**:
```json
{
  "success": true,
  "count": 10,
  "viaggi": [...]
}
```

---

### **GET** `/api/viaggi/{id}`
Dettaglio completo di un viaggio specifico

**Response**:
```json
{
  "success": true,
  "viaggio": {
    "_id": "...",
    "titolo": "Weekend alle Cinque Terre",
    "destinazione": "Cinque Terre, Italia",
    "partecipanti": [...],
    "attivita": [...],
    "spese": [...]
  }
}
```

---

## 🗄️ Database MongoDB Atlas

**Connection String**: Configurato in `backend/.env`

```
MONGODB_URI=mongodb+srv://Villanuevaprince_db:...@cluster0.rky3vjd.mongodb.net/
```

**Database**: `organizzazione_viaggi`  
**Collection**: `viaggi`  
**Documenti**: 10 viaggi pre-popolati

### Utenti nei Dati

- **mario.rossi** (Mario Rossi)
- **anna.verdi** (Anna Verdi)
- **luca.bianchi** (Luca Bianchi)

---

## 🎨 Frontend Features

### Schermata Login
- Input username con suggerimenti
- Validazione tramite API
- Error handling con messaggi chiari
- Loading state

### Dashboard Viaggi
- Header con utente loggato
- Griglia responsive di card viaggi
- Badge stato colorati (pianificazione, confermato, completato, annullato)
- Info rapide: destinazione, date, numero partecipanti

### Modal Dettaglio
- Informazioni complete viaggio
- Elenco partecipanti con avatar e stato
- Attività pianificate con date/orari
- Spese condivise con calcolo totale
- Chiusura con X, backdrop o ESC

### Design
- **Responsive**: Desktop, tablet, mobile
- **Moderno**: Gradients, shadows, animazioni
- **Accessibile**: Contrasti, focus states

---

## 🛠️ Tecnologie Utilizzate

### Backend
- **Flask** 3.0.0 - Framework web micro
- **Flask-CORS** 4.0.0 - Gestione CORS
- **PyMongo** 4.6.1 - Driver MongoDB
- **python-dotenv** - Gestione variabili ambiente

### Frontend
- **HTML5** - Struttura semantica
- **CSS3** - Grid, Flexbox, variabili CSS
- **JavaScript ES6+** - Fetch API, async/await, DOM manipulation

### Database
- **MongoDB Atlas** - Cloud database NoSQL

---

## 📋 Prerequisiti

- **Python** >= 3.8
- **pip** - Package manager Python
- **Browser moderno** (Chrome, Firefox, Safari, Edge)
- **Connessione internet** (per MongoDB Atlas)

---

## 🔧 Configurazione

### Backend (.env)
```env
MONGODB_URI=mongodb+srv://...
```

### Frontend (script.js)
```javascript
const API_BASE_URL = 'http://localhost:8000';
```

Modifica se backend è su host/porta diversi.

---

## 📖 Workflow Applicazione

1. **Login**: Utente inserisce username → API verifica esistenza
2. **Dashboard**: Carica tutti i viaggi da MongoDB
3. **Dettaglio**: Click su card → Modal con info complete
4. **Navigazione**: Esplora viaggi, chiudi modal, logout

---

## 🐛 Troubleshooting

### Backend non si avvia
- Verifica Python >= 3.8: `python --version`
- Reinstalla dipendenze: `pip install -r requirements.txt`
- Controlla `.env` con MONGODB_URI corretto

### Errore CORS
- Backend Flask ha già CORS abilitato con Flask-CORS
- Verifica `allow_origins` in `app.py`

### MongoDB non connette
- Controlla connessione internet
- Verifica MONGODB_URI in `.env`
- MongoDB Atlas IP Whitelist configurato (0.0.0.0/0)

### Frontend errore API
- Verifica backend attivo su porta 8000
- Apri console browser (F12) per dettagli
- Controlla `API_BASE_URL` in `script.js`

---

## 📝 Note Tecniche

### Login Semplificato
Questa è una applicazione **didattica** con autenticazione base:
- ✅ Verifica username esistente
- ❌ NO password
- ❌ NO JWT token
- ❌ NO sessioni persistenti

**Non usare in produzione senza sicurezza completa.**

### CORS Policy
Il backend accetta richieste da **tutti gli origin** (`allow_origins=["*"]`).  
In produzione, specifica domini precisi.

---

## 📚 Documentazione Dettagliata

- [Backend README](backend/README.md) - Dettagli API, struttura DB, esempi
- [Frontend README](frontend/README.md) - Design, personalizzazione, componenti

---

## ✅ Testing

### Test Backend
```bash
# Health check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"mario.rossi"}'

# Elenco viaggi
curl http://localhost:8000/api/viaggi

# Dettaglio viaggio (sostituisci {id} con _id reale)
curl http://localhost:8000/api/viaggi/{id}
```

### Test Frontend
1. Apri http://localhost:3000
2. Login con `mario.rossi`
3. Verifica lista viaggi visibile
4. Click su un viaggio → verifica modal
5. Chiudi modal → verifica funzioni
6. Logout → verifica ritorno a login

---

## 🎓 Obiettivi Didattici Raggiunti

✅ SPA funzionante senza framework  
✅ REST API con Flask  
✅ Integrazione MongoDB Atlas  
✅ CRUD operations (Read)  
✅ Error handling completo  
✅ Design responsive moderno  
✅ JavaScript asincrono (Fetch API)  
✅ Struttura progetto pulita  
✅ Documentazione completa  

---

## 📜 Licenza

Progetto didattico per esercizio informatica.

---

## 👤 Autore

**Villanuevaprince Lab**  
Repository: organizzazione_di_viaggi_di_gruppo

---

## 🚀 Deploy (Opzionale)

### Backend (esempio Railway/Render)
1. Push su GitHub
2. Collega repository a Railway/Render
3. Aggiungi env variable `MONGODB_URI`
4. Deploy automatico

### Frontend (esempio Netlify/Vercel)
1. Modifica `API_BASE_URL` con URL backend production
2. Push cartella `frontend/` su GitHub
3. Collega a Netlify/Vercel
4. Deploy automatico

---

**Enjoy! 🎉**