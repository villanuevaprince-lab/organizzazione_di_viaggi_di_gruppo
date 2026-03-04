from flask import Flask, request, jsonify, abort, session
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# Carica variabili ambiente
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "chiave-segreta-esame-viaggi-2026")

# Configurazione cookie per Codespaces cross-origin
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True  # Richiesto per SameSite=None

# Lista di origin sicuri per locale
LOCAL_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500"
]

def cors_origin():
    """
    Restituisce l'origin della richiesta se consentito,
    altrimenti None (Flask-CORS bloccherà l'origin)
    """
    origin = request.headers.get('Origin')
    if not origin:
        return None
    if origin in LOCAL_ORIGINS:
        return origin
    # Permetti tutti i subdomain di Codespaces su github.dev
    if origin.endswith(".app.github.dev"):
        return origin
    return None

# CORS Fix: usa callable per origin dinamico
CORS(app,
     origins=cors_origin,           # 🔹 callable per origin dinamico
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     expose_headers=["Content-Type"],
     supports_credentials=True,     # 🔹 necessario per sessioni
     max_age=3600
)

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

# Decorator per verificare login
def login_required(f):
    """Verifica che l'utente sia loggato"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({"success": False, "error": "Login richiesto"}), 401
        return f(*args, **kwargs)
    return decorated_function

# ROOT
@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "message": "API Viaggi di Gruppo - v2.0 (Flask + Sessioni)",
        "endpoints": {
            "login": "POST /api/login",
            "logout": "POST /api/logout",
            "session": "GET /api/session",
            "viaggi": "GET /api/viaggi",
            "dettaglio": "GET /api/viaggi/{id}",
            "nuovo": "POST /api/viaggi",
            "update": "PUT /api/viaggi/{id}",
            "partecipanti": "POST|DELETE /api/viaggi/{id}/partecipanti",
            "attivita": "POST|DELETE /api/viaggi/{id}/attivita",
            "spese": "POST|DELETE /api/viaggi/{id}/spese",
            "riepilogo": "GET /api/viaggi/{id}/spese/riepilogo",
            "pdf": "POST /api/viaggi/{id}/pdf"
        }
    })

# ENDPOINT: POST /api/login - Login con sessioni
@app.route("/api/login", methods=["POST"])
def login():
    """
    Verifica username esistente e salva in sessione
    Login semplice: solo username, cerca in creatore/partecipanti
    """
    data = request.get_json()
    
    if not data or 'username' not in data:
        return jsonify({"success": False, "error": "Username obbligatorio"}), 400
    
    username = data['username'].strip()
    
    if not username:
        return jsonify({"success": False, "error": "Username non può essere vuoto"}), 400
    
    try:
        # Cerca utente come creatore o partecipante
        utente_esistente = collection.find_one({
            "$or": [
                {"creatore.username": username},
                {"partecipanti.username": username}
            ]
        })
        
        if utente_esistente:
            # Salva in sessione
            session['username'] = username
            session.permanent = True
            return jsonify({
                "success": True,
                "message": f"Benvenuto {username}!",
                "username": username
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Utente '{username}' non trovato"
            }), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ENDPOINT: POST /api/logout - Logout
@app.route("/api/logout", methods=["POST"])
@login_required
def logout():
    """Cancella sessione utente"""
    username = session.get('username')
    session.clear()
    return jsonify({"success": True, "message": f"Arrivederci {username}!"})

# ENDPOINT: GET /api/session - Verifica sessione corrente
@app.route("/api/session", methods=["GET"])
def check_session():
    """Restituisce utente loggato o None"""
    if 'username' in session:
        return jsonify({"success": True, "username": session['username']})
    else:
        return jsonify({"success": False, "username": None})

# ENDPOINT 1: GET /api/viaggi - Elenco viaggi utente loggato
@app.route("/api/viaggi", methods=["GET"])
@login_required
def get_viaggi():
    """Restituisce viaggi dove utente è creatore O partecipante"""
    try:
        username = session['username']
        
        # Trova viaggi dove utente è creatore O partecipante
        viaggi = list(collection.find({
            "$or": [
                {"creatore.username": username},
                {"partecipanti.username": username}
            ]
        }))
        
        # Converti ObjectId
        for viaggio in viaggi:
            viaggio["_id"] = str(viaggio["_id"])
        
        return jsonify({
            "success": True,
            "count": len(viaggi),
            "viaggi": viaggi,
            "username": username
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ENDPOINT 2: GET /api/viaggi/:id - Dettaglio singolo viaggio
@app.route("/api/viaggi/<viaggio_id>", methods=["GET"])
@login_required
def get_viaggio_dettaglio(viaggio_id):
    """Restituisce dettagli viaggio completi"""
    try:
        if not ObjectId.is_valid(viaggio_id):
            return jsonify({"success": False, "error": "ID non valido"}), 400
        
        viaggio = collection.find_one({"_id": ObjectId(viaggio_id)})
        
        if not viaggio:
            return jsonify({"success": False, "error": "Viaggio non trovato"}), 404
        
        viaggio = viaggio_helper(viaggio)
        
        return jsonify({"success": True, "viaggio": viaggio})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ENDPOINT 3: POST /api/viaggi - Crea nuovo viaggio
@app.route("/api/viaggi", methods=["POST"])
@login_required
def create_viaggio():
    """Crea nuovo viaggio con utente loggato come creatore"""
    try:
        data = request.get_json()
        username = session['username']
        
        #Campi obbligatori
        if not data.get('titolo'):
            return jsonify({"success": False, "error": "Titolo obbligatorio"}), 400
        if not data.get('destinazione'):
            return jsonify({"success": False, "error": "Destinazione obbligatoria"}), 400
        if not data.get('periodo', {}).get('dataInizio'):
            return jsonify({"success": False, "error": "Data inizio obbligatoria"}), 400
        
        # Crea documento viaggio
        nuovo_viaggio = {
            "titolo": data['titolo'],
            "destinazione": data['destinazione'],
            "periodo": {
                "dataInizio": data['periodo']['dataInizio'],
                "dataFine": data['periodo'].get('dataFine')
            },
            "stato": data.get('stato', 'futuro'),
            "location": data.get('location'),  # {lat, lng}
            "creatore": {
                "id": username,
                "username": username,
                "nome": data.get('nomeCreatore', username.replace('.', ' ').title())
            },
            "partecipanti": data.get('partecipanti', []),
            "attivita": data.get('attivita', []),
            "spese": data.get('spese', []),
            "note": data.get('note'),
            "extra": data.get('extra'),
            "dataCreazione": datetime.utcnow()
        }
        
        result = collection.insert_one(nuovo_viaggio)
        nuovo_viaggio['_id'] = str(result.inserted_id)
        
        return jsonify({
            "success": True,
            "message": "Viaggio creato!",
            "viaggio": nuovo_viaggio
        }), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ENDPOINT 4: PUT /api/viaggi/<id> - Aggiorna viaggio
@app.route("/api/viaggi/<viaggio_id>", methods=["PUT"])
@login_required
def update_viaggio(viaggio_id):
    """Aggiorna viaggio esistente (solo creatore)"""
    try:
        if not ObjectId.is_valid(viaggio_id):
            return jsonify({"success": False, "error": "ID non valido"}), 400
        
        username = session['username']
        viaggio = collection.find_one({"_id": ObjectId(viaggio_id)})
        
        if not viaggio:
            return jsonify({"success": False, "error": "Viaggio non trovato"}), 404
        
        # Solo creatore può modificare
        if viaggio['creatore']['username'] != username:
            return jsonify({"success": False, "error": "Solo il creatore può modificare"}), 403
        
        data = request.get_json()
        
        # Campi aggiornabili
        update_fields = {}
        if 'titolo' in data:
            update_fields['titolo'] = data['titolo']
        if 'destinazione' in data:
            update_fields['destinazione'] = data['destinazione']
        if 'periodo' in data:
            update_fields['periodo'] = data['periodo']
        if 'stato' in data:
            update_fields['stato'] = data['stato']
        if 'location' in data:
            update_fields['location'] = data['location']
        if 'note' in data:
            update_fields['note'] = data['note']
        
        collection.update_one(
            {"_id": ObjectId(viaggio_id)},
            {"$set": update_fields}
        )
        
        return jsonify({"success": True, "message": "Viaggio aggiornato!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ENDPOINT 5: POST /api/viaggi/<id>/partecipanti - Aggiungi partecipante
@app.route("/api/viaggi/<viaggio_id>/partecipanti", methods=["POST"])
@login_required
def add_partecipante(viaggio_id):
    """Aggiungi partecipante al viaggio"""
    try:
        if not ObjectId.is_valid(viaggio_id):
            return jsonify({"success": False, "error": "ID non valido"}), 400
        
        data = request.get_json()
        if not data.get('username'):
            return jsonify({"success": False, "error": "Username obbligatorio"}), 400
        
        nuovo_partecipante = {
            "id": data['username'],
            "username": data['username'],
            "nome": data.get('nome', data['username'].replace('.', ' ').title()),
            "ruolo": data.get('ruolo', 'partecipante')
        }
        
        result = collection.update_one(
            {"_id": ObjectId(viaggio_id)},
            {"$addToSet": {"partecipanti": nuovo_partecipante}}
        )
        
        if result.modified_count > 0:
            return jsonify({"success": True, "message": "Partecipante aggiunto!"})
        else:
            return jsonify({"success": False, "error": "Partecipante già presente"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ENDPOINT 6: DELETE /api/viaggi/<id>/partecipanti/<username> - Rimuovi partecipante
@app.route("/api/viaggi/<viaggio_id>/partecipanti/<username>", methods=["DELETE"])
@login_required
def remove_partecipante(viaggio_id, username):
    """Rimuovi partecipante dal viaggio"""
    try:
        if not ObjectId.is_valid(viaggio_id):
            return jsonify({"success": False, "error": "ID non valido"}), 400
        
        result = collection.update_one(
            {"_id": ObjectId(viaggio_id)},
            {"$pull": {"partecipanti": {"username": username}}}
        )
        
        if result.modified_count > 0:
            return jsonify({"success": True, "message": "Partecipante rimosso!"})
        else:
            return jsonify({"success": False, "error": "Partecipante non trovato"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ENDPOINT 7: POST /api/viaggi/<id>/attivita - Aggiungi attività
@app.route("/api/viaggi/<viaggio_id>/attivita", methods=["POST"])
@login_required
def add_attivita(viaggio_id):
    """Aggiungi attività al viaggio"""
    try:
        if not ObjectId.is_valid(viaggio_id):
            return jsonify({"success": False, "error": "ID non valido"}), 400
        
        data = request.get_json()
        if not data.get('titolo'):
            return jsonify({"success": False, "error": "Titolo obbligatorio"}), 400
        
        nuova_attivita = {
            "titolo": data['titolo'],
            "tipo": data.get('tipo', 'visita'),
            "descrizione": data.get('descrizione'),
            "luogo": data.get('luogo'),
            "dataOra": data.get('dataOra'),
            "durataMinuti": data.get('durataMinuti'),
            "note": data.get('note')
        }
        
        result = collection.update_one(
            {"_id": ObjectId(viaggio_id)},
            {"$push": {"attivita": nuova_attivita}}
        )
        
        if result.modified_count > 0:
            return jsonify({"success": True, "message": "Attività aggiunta!"})
        else:
            return jsonify({"success": False, "error": "Viaggio non trovato"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ENDPOINT 8: DELETE /api/viaggi/<id>/attivita/<idx> - Rimuovi attività
@app.route("/api/viaggi/<viaggio_id>/attivita/<int:idx>", methods=["DELETE"])
@login_required
def remove_attivita(viaggio_id, idx):
    """Rimuovi attività dal viaggio"""
    try:
        if not ObjectId.is_valid(viaggio_id):
            return jsonify({"success": False, "error": "ID non valido"}), 400
        
        viaggio = collection.find_one({"_id": ObjectId(viaggio_id)})
        if not viaggio:
            return jsonify({"success": False, "error": "Viaggio non trovato"}), 404
        
        attivita = viaggio.get('attivita', [])
        if idx < 0 or idx >= len(attivita):
            return jsonify({"success": False, "error": "Indice non valido"}), 400
        
        attivita.pop(idx)
        
        collection.update_one(
            {"_id": ObjectId(viaggio_id)},
            {"$set": {"attivita": attivita}}
        )
        
        return jsonify({"success": True, "message": "Attività rimossa!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ENDPOINT 9: POST /api/viaggi/<id>/spese - Aggiungi spesa
@app.route("/api/viaggi/<viaggio_id>/spese", methods=["POST"])
@login_required
def add_spesa(viaggio_id):
    """Aggiungi spesa al viaggio"""
    try:
        if not ObjectId.is_valid(viaggio_id):
            return jsonify({"success": False, "error": "ID non valido"}), 400
        
        data = request.get_json()
        if not data.get('descrizione'):
            return jsonify({"success": False, "error": "Descrizione obbligatoria"}), 400
        if 'importo' not in data:
            return jsonify({"success": False, "error": "Importo obbligatorio"}), 400
        
        nuova_spesa = {
            "descrizione": data['descrizione'],
            "categoria": data.get('categoria', 'varie'),
            "importo": float(data['importo']),
            "valuta": data.get('valuta', 'EUR'),
            "pagatore": {
                "username": session['username'],
                "nome": session['username'].replace('.', ' ').title()
            },
            "data": data.get('data', datetime.utcnow().isoformat()),
            "note": data.get('note')
        }
        
        result = collection.update_one(
            {"_id": ObjectId(viaggio_id)},
            {"$push": {"spese": nuova_spesa}}
        )
        
        if result.modified_count > 0:
            return jsonify({"success": True, "message": "Spesa aggiunta!"})
        else:
            return jsonify({"success": False, "error": "Viaggio non trovato"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ENDPOINT 10: DELETE /api/viaggi/<id>/spese/<idx> - Rimuovi spesa
@app.route("/api/viaggi/<viaggio_id>/spese/<int:idx>", methods=["DELETE"])
@login_required
def remove_spesa(viaggio_id, idx):
    """Rimuovi spesa dal viaggio"""
    try:
        if not ObjectId.is_valid(viaggio_id):
            return jsonify({"success": False, "error": "ID non valido"}), 400
        
        viaggio = collection.find_one({"_id": ObjectId(viaggio_id)})
        if not viaggio:
            return jsonify({"success": False, "error": "Viaggio non trovato"}), 404
        
        spese = viaggio.get('spese', [])
        if idx < 0 or idx >= len(spese):
            return jsonify({"success": False, "error": "Indice non valido"}), 400
        
        spese.pop(idx)
        
        collection.update_one(
            {"_id": ObjectId(viaggio_id)},
            {"$set": {"spese": spese}}
        )
        
        return jsonify({"success": True, "message": "Spesa rimossa!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ENDPOINT 11: GET /api/viaggi/<id>/spese/riepilogo - Riepilogo spese
@app.route("/api/viaggi/<viaggio_id>/spese/riepilogo", methods=["GET"])
@login_required
def riepilogo_spese(viaggio_id):
    """Calcola totale e riepilogo per categoria"""
    try:
        if not ObjectId.is_valid(viaggio_id):
            return jsonify({"success": False, "error": "ID non valido"}), 400
        
        viaggio = collection.find_one({"_id": ObjectId(viaggio_id)})
        if not viaggio:
            return jsonify({"success": False, "error": "Viaggio non trovato"}), 404
        
        spese = viaggio.get('spese', [])
        
        totale = sum(s.get('importo', 0) for s in spese)
        
        # Raggruppa per categoria
        per_categoria = {}
        for spesa in spese:
            cat = spesa.get('categoria', 'varie')
            if cat not in per_categoria:
                per_categoria[cat] = 0
            per_categoria[cat] += spesa.get('importo', 0)
        
        return jsonify({
            "success": True,
            "totale": totale,
            "valuta": spese[0].get('valuta', 'EUR') if spese else 'EUR',
            "perCategoria": per_categoria,
            "numeroSpese": len(spese)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ENDPOINT 12: POST /api/viaggi/<id>/pdf - Genera PDF viaggio
@app.route("/api/viaggi/<viaggio_id>/pdf", methods=["POST"])
@login_required
def genera_pdf(viaggio_id):
    """Genera PDF con tutti i dettagli del viaggio"""
    try:
        if not ObjectId.is_valid(viaggio_id):
            return jsonify({"success": False, "error": "ID non valido"}), 400
        
        viaggio = collection.find_one({"_id": ObjectId(viaggio_id)})
        if not viaggio:
            return jsonify({"success": False, "error": "Viaggio non trovato"}), 404
        
        # Crea PDF in memoria
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Header
        p.setFont("Helvetica-Bold", 20)
        p.drawString(inch, height - inch, f"Viaggio: {viaggio.get('titolo', 'N/A')}")
        
        p.setFont("Helvetica", 12)
        y = height - 1.5*inch
        
        # Informazioni generali
        p.drawString(inch, y, f"Destinazione: {viaggio.get('destinazione', 'N/A')}")
        y -= 0.3*inch
        
        periodo = viaggio.get('periodo', {})
        p.drawString(inch, y, f"Periodo: {periodo.get('dataInizio', 'N/A')} - {periodo.get('dataFine', 'N/A')}")
        y -= 0.3*inch
        
        p.drawString(inch, y, f"Stato: {viaggio.get('stato', 'N/A')}")
        y -= 0.5*inch
        
        # Partecipanti
        partecipanti = viaggio.get('partecipanti', [])
        p.setFont("Helvetica-Bold", 14)
        p.drawString(inch, y, f"Partecipanti ({len(partecipanti)}):")
        y -= 0.3*inch
        
        p.setFont("Helvetica", 10)
        for part in partecipanti[:10]:  # Max 10
            p.drawString(1.2*inch, y, f"- {part.get('nome', part.get('username', 'N/A'))}")
            y -= 0.2*inch
        
        y -= 0.3*inch
        
        # Attività
        attivita = viaggio.get('attivita', [])
        p.setFont("Helvetica-Bold", 14)
        p.drawString(inch, y, f"Attività ({len(attivita)}):")
        y -= 0.3*inch
        
        p.setFont("Helvetica", 10)
        for att in attivita[:8]:  # Max 8
            p.drawString(1.2*inch, y, f"- {att.get('titolo', 'N/A')} ({att.get('tipo', 'N/A')})")
            y -= 0.2*inch
        
        y -= 0.3*inch
        
        # Spese
        spese = viaggio.get('spese', [])
        totale_spese = sum(s.get('importo', 0) for s in spese)
        
        p.setFont("Helvetica-Bold", 14)
        p.drawString(inch, y, f"Spese ({len(spese)}) - Totale: {totale_spese:.2f} EUR")
        y -= 0.3*inch
        
        p.setFont("Helvetica", 10)
        for spesa in spese[:10]:  # Max 10
            p.drawString(1.2*inch, y, f"- {spesa.get('descrizione', 'N/A')}: {spesa.get('importo', 0):.2f} EUR")
            y -= 0.2*inch
        
        # Footer
        p.setFont("Helvetica-Oblique", 8)
        p.drawString(inch, 0.5*inch, f"Generato il {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        p.showPage()
        p.save()
        
        buffer.seek(0)
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Restituisci PDF come base64
        import base64
        pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
        
        return jsonify({
            "success": True,
            "pdf": pdf_base64,
            "filename": f"viaggio_{viaggio.get('titolo', 'documento').replace(' ', '_')}.pdf"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

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
