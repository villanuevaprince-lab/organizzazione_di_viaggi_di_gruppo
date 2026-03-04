# 🚀 Backend API - Viaggi di Gruppo

API REST sviluppata con **FastAPI** per gestire l'organizzazione di viaggi di gruppo.

## 📦 Installazione

```bash
# Dalla cartella backend
cd backend

# Installa dipendenze
pip install -r requirements.txt
```

## 🔧 Configurazione

Il file `.env` contiene la connessione MongoDB Atlas:
```
MONGODB_URI=mongodb+srv://...
```

## ▶️ Avvio Server

```bash
# Modalità development con auto-reload
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Il server sarà disponibile su:
- **API**: http://localhost:8000
- **Documentazione Swagger**: http://localhost:8000/docs
- **Redoc**: http://localhost:8000/redoc

## 🔌 Endpoint API

### 1. Login Utente
```http
POST /api/login
Content-Type: application/json

{
  "username": "mario.rossi"
}
```

**Utenti esistenti**: `mario.rossi`, `anna.verdi`, `luca.bianchi`

**Risposta OK**:
```json
{
  "success": true,
  "message": "Benvenuto mario.rossi!",
  "username": "mario.rossi"
}
```

**Errore 404**: Utente non trovato nei viaggi

---

### 2. Elenco Viaggi
```http
GET /api/viaggi
```

**Risposta**:
```json
{
  "success": true,
  "count": 10,
  "viaggi": [
    {
      "_id": "...",
      "titolo": "Weekend alle Cinque Terre",
      "destinazione": "Cinque Terre, Italia",
      "stato": "pianificazione",
      "creatore": { "username": "mario.rossi", "nome": "Mario Rossi" },
      ...
    }
  ]
}
```

---

### 3. Dettaglio Viaggio
```http
GET /api/viaggi/{viaggio_id}
```

**Esempio**: `/api/viaggi/507f1f77bcf86cd799439011`

**Risposta**:
```json
{
  "success": true,
  "viaggio": {
    "_id": "507f1f77bcf86cd799439011",
    "titolo": "Weekend alle Cinque Terre",
    "destinazione": "Cinque Terre, Italia",
    "data_inizio": "2024-06-15",
    "data_fine": "2024-06-17",
    "stato": "pianificazione",
    "partecipanti": [...],
    "attivita": [...],
    "spese": [...]
  }
}
```

**Errore 400**: ID non valido  
**Errore 404**: Viaggio non trovato

---

### 4. Health Check
```http
GET /health
```

Verifica connessione database.

## 🗄️ Database MongoDB Atlas

**Database**: `organizzazione_viaggi`  
**Collection**: `viaggi`  
**Documenti**: 10 viaggi pre-popolati

### Struttura Documento Viaggio

```json
{
  "_id": ObjectId,
  "titolo": "string",
  "destinazione": "string",
  "descrizione": "string (opzionale)",
  "data_inizio": "YYYY-MM-DD",
  "data_fine": "YYYY-MM-DD",
  "stato": "pianificazione | confermato | completato | annullato",
  "creatore": {
    "username": "string",
    "nome": "string"
  },
  "partecipanti": [
    {
      "username": "string",
      "nome": "string",
      "confermato": boolean
    }
  ],
  "attivita": [
    {
      "titolo": "string",
      "descrizione": "string",
      "data": "YYYY-MM-DD",
      "orario": "HH:MM"
    }
  ],
  "spese": [
    {
      "descrizione": "string",
      "importo": number,
      "valuta": "EUR",
      "pagato_da": "username",
      "divisa_tra": ["username1", "username2"]
    }
  ]
}
```

## 🛡️ Sicurezza

- **CORS**: Abilitato per tutti gli origin (in produzione specificare domini)
- **Login**: Semplice verifica username (no password, no JWT)
- **Validazione**: ObjectId MongoDB verificato prima delle query

## 🐛 Troubleshooting

**Errore connessione MongoDB**:
- Verifica `.env` con MONGODB_URI corretto
- Controlla connessione internet
- Atlas IP Whitelist configurato (0.0.0.0/0 per tutti)

**Porta 8000 già in uso**:
```bash
uvicorn app:app --reload --port 8001
```

## 📝 Note Tecniche

- **Framework**: FastAPI 0.109.0
- **Driver MongoDB**: PyMongo 4.6.1
- **Validazione**: Pydantic 2.5.3
- **ASGI Server**: Uvicorn
- **Python**: >= 3.8
