from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
from typing import Optional, List
import os
from dotenv import load_dotenv

# Carica variabili ambiente
load_dotenv()

app = FastAPI(title="API Viaggi di Gruppo", version="1.0.0")

# Configurazione CORS per GitHub Codespaces e sviluppo locale
# Nota: allow_credentials=True NON è compatibile con allow_origins=["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permetti tutti gli origin
    allow_credentials=False,  # Disabilita credentials per permettere wildcard
    allow_methods=["*"],  # Permetti tutti i metodi HTTP
    allow_headers=["*"],  # Permetti tutti gli header
)

# Connessione MongoDB
MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise ValueError("MONGODB_URI non trovato nel file .env")

client = MongoClient(MONGODB_URI)
db = client.organizzazione_viaggi
collection = db.viaggi

# Modelli Pydantic
class LoginRequest(BaseModel):
    username: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    username: Optional[str] = None

# Helper per convertire ObjectId in stringa
def viaggio_helper(viaggio) -> dict:
    """Converte il viaggio MongoDB in dict serializzabile JSON"""
    if viaggio is None:
        return None
    
    viaggio["_id"] = str(viaggio["_id"])
    return viaggio

# ROOT
@app.get("/")
def root():
    return {
        "message": "API Viaggi di Gruppo - v1.0",
        "endpoints": {
            "login": "POST /api/login",
            "viaggi": "GET /api/viaggi",
            "dettaglio": "GET /api/viaggi/{id}"
        }
    }

# ENDPOINT 1: GET /api/viaggi - Elenco tutti i viaggi
@app.get("/api/viaggi")
def get_viaggi():
    """Restituisce l'elenco di tutti i viaggi nel database"""
    try:
        viaggi = list(collection.find())
        
        # Converti ObjectId in stringa per ogni viaggio
        for viaggio in viaggi:
            viaggio["_id"] = str(viaggio["_id"])
        
        return {
            "success": True,
            "count": len(viaggi),
            "viaggi": viaggi
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore database: {str(e)}")

# ENDPOINT 2: GET /api/viaggi/:id - Dettaglio singolo viaggio
@app.get("/api/viaggi/{viaggio_id}")
def get_viaggio_dettaglio(viaggio_id: str):
    """Restituisce i dettagli di un viaggio specifico"""
    try:
        # Verifica che l'ID sia valido
        if not ObjectId.is_valid(viaggio_id):
            raise HTTPException(status_code=400, detail="ID viaggio non valido")
        
        viaggio = collection.find_one({"_id": ObjectId(viaggio_id)})
        
        if not viaggio:
            raise HTTPException(status_code=404, detail="Viaggio non trovato")
        
        # Converti ObjectId
        viaggio = viaggio_helper(viaggio)
        
        return {
            "success": True,
            "viaggio": viaggio
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore database: {str(e)}")

# ENDPOINT 3: POST /api/login - Login utente semplice
@app.post("/api/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """
    Verifica se un utente esiste nei viaggi (come creatore o partecipante)
    Login semplice: solo username, no password
    """
    username = request.username.strip()
    
    if not username:
        raise HTTPException(status_code=400, detail="Username obbligatorio")
    
    try:
        # Cerca utente come creatore
        viaggio_creatore = collection.find_one({"creatore.username": username})
        
        # Cerca utente nei partecipanti
        viaggio_partecipante = collection.find_one({"partecipanti.username": username})
        
        if viaggio_creatore or viaggio_partecipante:
            return LoginResponse(
                success=True,
                message=f"Benvenuto {username}!",
                username=username
            )
        else:
            raise HTTPException(
                status_code=404, 
                detail=f"Utente '{username}' non trovato nei viaggi esistenti"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore database: {str(e)}")

# Health check
@app.get("/health")
def health_check():
    """Verifica stato connessione database"""
    try:
        # Ping database
        client.admin.command('ping')
        count = collection.count_documents({})
        return {
            "status": "healthy",
            "database": "connected",
            "viaggi_count": count
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
