# ⚡ Quick Start - GitHub Codespaces

## 🚀 Applicazione Attiva!

Entrambi i server sono già in esecuzione:

### 🔌 Backend API (FastAPI)
**URL**: https://literate-space-bassoon-wrqgp95qrr54c5vj9-8000.app.github.dev  
**Documentazione**: Aggiungi `/docs` all'URL sopra

### 🌐 Frontend SPA  
**URL**: https://literate-space-bassoon-wrqgp95qrr54c5vj9-5500.app.github.dev

---

## 🎯 Come Accedere

### Metodo 1: Pannello Porte (Consigliato)
1. In VS Code, vai al pannello **PORTS** (in basso)
2. Cerca la porta **5500** (Frontend)
3. Click sull'icona 🌐 "Open in Browser" accanto alla porta
4. Il frontend si aprirà e si connetterà automaticamente al backend!

### Metodo 2: URL Diretto
Apri questo URL nel browser:
```
https://literate-space-bassoon-wrqgp95qrr54c5vj9-5500.app.github.dev
```

---

## 🔐 Login

Usa uno di questi username (senza password):
- `mario.rossi`
- `anna.verdi`
- `luca.bianchi`

---

## ✅ Verifica Servizi

### Test Backend
```bash
curl https://literate-space-bassoon-wrqgp95qrr54c5vj9-8000.app.github.dev/health
```

### Test Connessione Database
```bash
curl https://literate-space-bassoon-wrqgp95qrr54c5vj9-8000.app.github.dev/api/viaggi
```

---

## 🔧 Riavvio Servizi (se necessario)

### Backend
```bash
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
python3 -m http.server 5500
```

---

## 🐛 Troubleshooting

### Errore "ERR_CONNECTION_REFUSED"
- ✅ **Risolto**: Il frontend ora rileva automaticamente l'ambiente Codespaces
- Assicurati di aprire il frontend tramite il port forwarding (porta 5500)

### Porte non visibili nel pannello
1. Apri il pannello PORTS
2. Click su "Forward a Port"
3. Aggiungi: 8000 (backend) e 5500 (frontend)
4. Imposta visibilità su "Public" se necessario

### CORS Error
- Non dovrebbe succedere, il backend ha CORS configurato per tutti gli origin
- Verifica che entrambi i servizi usino HTTPS (Codespaces forza HTTPS)

---

## 📱 Test Funzionalità

1. **Login**: Inserisci username → Verifica accesso
2. **Elenco Viaggi**: 10 viaggi visualizzati
3. **Dettaglio**: Click su card → Modal con info complete
4. **Responsive**: Testa su diverse dimensioni finestra

---

## 📊 Port Forwarding Status

| Porta | Servizio | URL |
|-------|----------|-----|
| 8000  | Backend  | https://...-8000.app.github.dev |
| 5500  | Frontend | https://...-5500.app.github.dev |

Il frontend JavaScript rileva automaticamente l'ambiente e si connette al backend corretto! 🎉
