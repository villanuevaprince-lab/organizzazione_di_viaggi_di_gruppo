from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv

# Carica variabili ambiente
load_dotenv()

app = Flask(__name__)

# Configurazione CORS per GitHub Codespaces e sviluppo locale
# Configurazione esplicita per gestire correttamente le preflight requests
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type"],
        "supports_credentials": False,
        "max_age": 3600
    }
})

# Connessione MongoDB
MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise ValueError("MONGODB_URI non trovato nel file .env")

client = MongoClient(MONGODB_URI)
db = client.organizzazione_viaggi
collection = db.viaggi

# Helper per convertire ObjectId in stringa
def viaggio_helper(viaggio):
    """Converte il viaggio MongoDB in dict serializzabile JSON"""
    if viaggio is None:
        return None
    
    viaggio["_id"] = str(viaggio["_id"])
    return viaggio

# ROOT
@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "message": "API Viaggi di Gruppo - v1.0 (Flask)",
        "endpoints": {
            "login": "POST /api/login",
            "viaggi": "GET /api/viaggi",
            "dettaglio": "GET /api/viaggi/{id}"
        }
    })

# ENDPOINT 1: GET /api/viaggi - Elenco tutti i viaggi
@app.route("/api/viaggi", methods=["GET"])
def get_viaggi():
    """Restituisce l'elenco di tutti i viaggi nel database"""
    try:
        viaggi = list(collection.find())
        
        # Converti ObjectId in stringa per ogni viaggio
        for viaggio in viaggi:
            viaggio["_id"] = str(viaggio["_id"])
        
        return jsonify({
            "success": True,
            "count": len(viaggi),
            "viaggi": viaggi
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Errore database: {str(e)}"
        }), 500

# ENDPOINT 2: GET /api/viaggi/:id - Dettaglio singolo viaggio
@app.route("/api/viaggi/<viaggio_id>", methods=["GET"])
def get_viaggio_dettaglio(viaggio_id):
    """Restituisce i dettagli di un viaggio specifico"""
    try:
        # Verifica che l'ID sia valido
        if not ObjectId.is_valid(viaggio_id):
            return jsonify({
                "success": False,
                "detail": "ID viaggio non valido"
            }), 400
        
        viaggio = collection.find_one({"_id": ObjectId(viaggio_id)})
        
        if not viaggio:
            return jsonify({
                "success": False,
                "detail": "Viaggio non trovato"
            }), 404
        
        # Converti ObjectId
        viaggio = viaggio_helper(viaggio)
        
        return jsonify({
            "success": True,
            "viaggio": viaggio
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "detail": f"Errore database: {str(e)}"
        }), 500

# ENDPOINT 3: POST /api/login - Login utente semplice
@app.route("/api/login", methods=["POST"])
def login():
    """
    Verifica se un utente esiste nei viaggi (come creatore o partecipante)
    Login semplice: solo username, no password
    """
    data = request.get_json()
    
    if not data or 'username' not in data:
        return jsonify({
            "success": False,
            "detail": "Username obbligatorio"
        }), 400
    
    username = data['username'].strip()
    
    if not username:
        return jsonify({
            "success": False,
            "detail": "Username obbligatorio"
        }), 400
    
    try:
        # Cerca utente come creatore
        viaggio_creatore = collection.find_one({"creatore.username": username})
        
        # Cerca utente nei partecipanti
        viaggio_partecipante = collection.find_one({"partecipanti.username": username})
        
        if viaggio_creatore or viaggio_partecipante:
            return jsonify({
                "success": True,
                "message": f"Benvenuto {username}!",
                "username": username
            })
        else:
            return jsonify({
                "success": False,
                "detail": f"Utente '{username}' non trovato nei viaggi esistenti"
            }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "detail": f"Errore database: {str(e)}"
        }), 500

# Health check
@app.route("/health", methods=["GET"])
def health_check():
    """Verifica stato connessione database"""
    try:
        # Ping database
        client.admin.command('ping')
        count = collection.count_documents({})
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "viaggi_count": count
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

# Entry point per esecuzione diretta
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
