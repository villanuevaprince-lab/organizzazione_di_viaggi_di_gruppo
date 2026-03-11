from flask import Flask, request, jsonify, session
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os
import base64
from dotenv import load_dotenv
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# Carica variabili ambiente
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "chiave-segreta-esame-viaggi-2026")

# Configurazione cookie in base all'ambiente (Codespaces vs locale)
if os.getenv('CODESPACES'):
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    app.config['SESSION_COOKIE_SECURE'] = True
else:
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = False

# CORS con Flask-CORS: origin sicuri per locale e Codespaces
ALLOWED_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

def check_origin(origin):
    """Verifica se un origin è consentito (locale o Codespaces)"""
    if not origin:
        return False
    if origin in ALLOWED_ORIGINS:
        return True
    if origin.endswith(".app.github.dev"):
        return True
    return False

@app.after_request
def add_cors_headers(response):
    """Aggiunge header CORS per supportare sia locale che Codespaces"""
    origin = request.headers.get('Origin')
    if origin and check_origin(origin):
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Expose-Headers'] = 'Content-Type'
        response.headers['Access-Control-Max-Age'] = '3600'
    return response

@app.before_request
def handle_preflight():
    """Gestisce richieste preflight OPTIONS"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

# Connessione MongoDB
MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise ValueError("MONGODB_URI non trovato nel file .env")

client = MongoClient(MONGODB_URI)
db = client.organizzazione_viaggi
collection = db.viaggi
utenti_collection = db.utenti

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

# ENDPOINT: POST /api/login - Login con credenziali
@app.route("/api/login", methods=["POST"])
def login():
    """Verifica credenziali (username + password) nella collezione utenti"""
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"success": False, "error": "Username e password obbligatori"}), 400

    username = data['username'].strip()
    password = data['password']

    if not username or not password:
        return jsonify({"success": False, "error": "I campi non possono essere vuoti"}), 400

    try:
        # Cerca utente nella collezione utenti (.find_one)
        utente = utenti_collection.find_one({"username": username})

        if utente and check_password_hash(utente['password'], password):
            session['username'] = username
            session['nome'] = utente.get('nome', username)
            session.permanent = True
            return jsonify({
                "success": True,
                "message": f"Benvenuto {utente.get('nome', username)}!",
                "username": username,
                "nome": utente.get('nome', username)
            })
        else:
            return jsonify({
                "success": False,
                "error": "Credenziali non valide"
            }), 401
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
        return jsonify({
            "success": True,
            "username": session['username'],
            "nome": session.get('nome', session['username'])
        })
    else:
        return jsonify({"success": False, "username": None})

# ENDPOINT 1: GET /api/viaggi - Elenco tutti i viaggi (usa .find())
@app.route("/api/viaggi", methods=["GET"])
@login_required
def get_viaggi():
    """Restituisce tutti i viaggi disponibili usando .find()"""
    try:
        username = session['username']

        # Usa .find() per ottenere tutti i viaggi
        viaggi = list(collection.find({}))

        # Converti ObjectId in stringa per JSON
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
        
        # Converti date stringa in datetime per schema MongoDB
        data_inizio = datetime.fromisoformat(data['periodo']['dataInizio'])
        data_fine = datetime.fromisoformat(data['periodo']['dataFine']) if data['periodo'].get('dataFine') else None
        
        # Crea documento seguendo lo schema di validazione MongoDB
        location = None
        if data.get('location') and data['location'].get('lat') and data['location'].get('lng'):
            location = {
                "lat": float(data['location']['lat']),
                "lng": float(data['location']['lng'])
            }
        
        now = datetime.utcnow()
        nuovo_viaggio = {
            "titolo": data['titolo'],
            "destinazione": data['destinazione'],
            "periodo": {
                "dataInizio": data_inizio,
                "dataFine": data_fine
            },
            "descrizione": data.get('descrizione', None),
            "stato": data.get('stato', 'futuro'),
            "location": location,
            "creatore": {
                "id": username,
                "username": username,
                "nome": session.get('nome', username)
            },
            "partecipanti": [],
            "attivita": [],
            "spese": [],
            "note": data.get('note', None),
            "extra": None,
            "dataCreazione": now,
            "ultimaModifica": now
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
        update_fields = {"ultimaModifica": datetime.utcnow()}
        if 'titolo' in data:
            update_fields['titolo'] = data['titolo']
        if 'destinazione' in data:
            update_fields['destinazione'] = data['destinazione']
        if 'periodo' in data:
            periodo = {}
            if data['periodo'].get('dataInizio'):
                periodo['dataInizio'] = datetime.fromisoformat(data['periodo']['dataInizio'])
            if data['periodo'].get('dataFine'):
                periodo['dataFine'] = datetime.fromisoformat(data['periodo']['dataFine'])
            else:
                periodo['dataFine'] = None
            update_fields['periodo'] = periodo
        if 'stato' in data:
            update_fields['stato'] = data['stato']
        if 'location' in data:
            update_fields['location'] = data['location']
        if 'note' in data:
            update_fields['note'] = data['note']
        if 'descrizione' in data:
            update_fields['descrizione'] = data['descrizione']
        
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
    """Aggiungi partecipante al viaggio (schema: id, nome, note)"""
    try:
        if not ObjectId.is_valid(viaggio_id):
            return jsonify({"success": False, "error": "ID non valido"}), 400
        
        data = request.get_json()
        if not data.get('id'):
            return jsonify({"success": False, "error": "ID partecipante obbligatorio"}), 400
        
        # Schema: partecipanti = {id, nome, note}
        nuovo_partecipante = {
            "id": data['id'],
            "nome": data.get('nome', data['id'].replace('.', ' ').title()),
            "note": data.get('note', None)
        }
        
        # Verifica se già presente
        viaggio = collection.find_one({"_id": ObjectId(viaggio_id)})
        if not viaggio:
            return jsonify({"success": False, "error": "Viaggio non trovato"}), 404
        
        partecipanti = viaggio.get('partecipanti', [])
        if any(p.get('id') == data['id'] for p in partecipanti):
            return jsonify({"success": False, "error": "Partecipante già presente"}), 400
        
        collection.update_one(
            {"_id": ObjectId(viaggio_id)},
            {
                "$push": {"partecipanti": nuovo_partecipante},
                "$set": {"ultimaModifica": datetime.utcnow()}
            }
        )
        
        return jsonify({"success": True, "message": "Partecipante aggiunto!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ENDPOINT 6: DELETE /api/viaggi/<id>/partecipanti/<part_id> - Rimuovi partecipante
@app.route("/api/viaggi/<viaggio_id>/partecipanti/<part_id>", methods=["DELETE"])
@login_required
def remove_partecipante(viaggio_id, part_id):
    """Rimuovi partecipante dal viaggio (usa campo 'id')"""
    try:
        if not ObjectId.is_valid(viaggio_id):
            return jsonify({"success": False, "error": "ID non valido"}), 400
        
        result = collection.update_one(
            {"_id": ObjectId(viaggio_id)},
            {
                "$pull": {"partecipanti": {"id": part_id}},
                "$set": {"ultimaModifica": datetime.utcnow()}
            }
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
        
        # Schema attivita: {titolo, tipo, dataOra(date|null), luogo, descrizione, durataMinuti(int|null), note}
        data_ora = None
        if data.get('dataOra'):
            data_ora = datetime.fromisoformat(data['dataOra'])
        
        durata = None
        if data.get('durataMinuti') is not None:
            durata = int(data['durataMinuti'])
        
        nuova_attivita = {
            "titolo": data['titolo'],
            "tipo": data.get('tipo', None),
            "dataOra": data_ora,
            "luogo": data.get('luogo', None),
            "descrizione": data.get('descrizione', None),
            "durataMinuti": durata,
            "note": data.get('note', None)
        }
        
        result = collection.update_one(
            {"_id": ObjectId(viaggio_id)},
            {
                "$push": {"attivita": nuova_attivita},
                "$set": {"ultimaModifica": datetime.utcnow()}
            }
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
            {"$set": {"attivita": attivita, "ultimaModifica": datetime.utcnow()}}
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
        
        # Schema spese: {categoria, descrizione, importo, valuta, pagatore:{id,nome}, data, ...}
        nuova_spesa = {
            "categoria": data.get('categoria', 'varie'),
            "descrizione": data['descrizione'],
            "importo": float(data['importo']),
            "valuta": data.get('valuta', 'EUR'),
            "pagatore": {
                "id": session['username'],
                "nome": session.get('nome', session['username'])
            },
            "divisaTra": None,
            "data": datetime.utcnow(),
            "ricevutaUrl": None
        }
        
        result = collection.update_one(
            {"_id": ObjectId(viaggio_id)},
            {
                "$push": {"spese": nuova_spesa},
                "$set": {"ultimaModifica": datetime.utcnow()}
            }
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
            {"$set": {"spese": spese, "ultimaModifica": datetime.utcnow()}}
        )
        
        return jsonify({"success": True, "message": "Spesa rimossa!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ENDPOINT 11: GET /api/viaggi/<id>/spese/riepilogo - Riepilogo spese con aggregate()
@app.route("/api/viaggi/<viaggio_id>/spese/riepilogo", methods=["GET"])
@login_required
def riepilogo_spese(viaggio_id):
    """Calcola totale e riepilogo per categoria usando aggregate()"""
    try:
        if not ObjectId.is_valid(viaggio_id):
            return jsonify({"success": False, "error": "ID non valido"}), 400

        # Verifica esistenza viaggio
        viaggio = collection.find_one({"_id": ObjectId(viaggio_id)})
        if not viaggio:
            return jsonify({"success": False, "error": "Viaggio non trovato"}), 404

        # Usa aggregate() per raggruppare spese per categoria
        pipeline = [
            {"$match": {"_id": ObjectId(viaggio_id)}},
            {"$project": {"spese": {"$ifNull": ["$spese", []]}}},
            {"$unwind": {"path": "$spese", "preserveNullAndEmptyArrays": False}},
            {"$group": {
                "_id": "$spese.categoria",
                "totale": {"$sum": "$spese.importo"},
                "count": {"$sum": 1}
            }},
            {"$sort": {"totale": -1}}
        ]

        risultati = list(collection.aggregate(pipeline))

        per_categoria = {}
        totale = 0
        numero_spese = 0

        for r in risultati:
            if r["_id"] is not None:
                per_categoria[r["_id"]] = round(r["totale"], 2)
                totale += r["totale"]
                numero_spese += r["count"]

        return jsonify({
            "success": True,
            "totale": round(totale, 2),
            "valuta": "EUR",
            "perCategoria": per_categoria,
            "numeroSpese": numero_spese
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

# =====================================================
# SEED DATABASE - Popola con dati di esempio
# =====================================================

def seed_database():
    """Popola il database con 3 utenti e 10 viaggi di esempio se vuoto"""

    # --- Seed utenti ---
    if utenti_collection.count_documents({}) == 0:
        print("Popolo collezione utenti...")
        utenti = [
            {
                "username": "mario.rossi",
                "password": generate_password_hash("mario123"),
                "nome": "Mario Rossi",
                "email": "mario.rossi@email.com"
            },
            {
                "username": "anna.verdi",
                "password": generate_password_hash("anna123"),
                "nome": "Anna Verdi",
                "email": "anna.verdi@email.com"
            },
            {
                "username": "luca.bianchi",
                "password": generate_password_hash("luca123"),
                "nome": "Luca Bianchi",
                "email": "luca.bianchi@email.com"
            }
        ]
        utenti_collection.insert_many(utenti)
        print(f"{len(utenti)} utenti inseriti")

    # --- Seed viaggi ---
    if collection.count_documents({}) == 0:
        print("Popolo collezione viaggi...")

        c_mario = {"id": "mario.rossi", "username": "mario.rossi", "nome": "Mario Rossi"}
        c_anna = {"id": "anna.verdi", "username": "anna.verdi", "nome": "Anna Verdi"}
        c_luca = {"id": "luca.bianchi", "username": "luca.bianchi", "nome": "Luca Bianchi"}

        p_mario = {"id": "mario.rossi", "nome": "Mario Rossi", "note": None}
        p_anna = {"id": "anna.verdi", "nome": "Anna Verdi", "note": None}
        p_luca = {"id": "luca.bianchi", "nome": "Luca Bianchi", "note": None}

        viaggi_seed = [
            {
                "titolo": "Weekend a Roma",
                "destinazione": "Roma, Italia",
                "periodo": {"dataInizio": "2025-03-15", "dataFine": "2025-03-17"},
                "stato": "concluso",
                "location": {"lat": 41.9028, "lng": 12.4964},
                "creatore": c_mario,
                "partecipanti": [p_anna, p_luca],
                "attivita": [
                    {"titolo": "Visita al Colosseo", "tipo": "visita", "descrizione": "Tour guidato del Colosseo e Foro Romano", "luogo": "Colosseo"},
                    {"titolo": "Pranzo a Trastevere", "tipo": "pasto", "descrizione": "Pranzo tipico romano", "luogo": "Trastevere"}
                ],
                "spese": [
                    {"descrizione": "Hotel 2 notti", "categoria": "alloggio", "importo": 280.0, "valuta": "EUR", "pagatore": {"id": "mario.rossi", "nome": "Mario Rossi"}},
                    {"descrizione": "Biglietti Colosseo", "categoria": "attivita", "importo": 48.0, "valuta": "EUR", "pagatore": {"id": "anna.verdi", "nome": "Anna Verdi"}},
                    {"descrizione": "Cena Trastevere", "categoria": "cibo", "importo": 95.0, "valuta": "EUR", "pagatore": {"id": "luca.bianchi", "nome": "Luca Bianchi"}}
                ],
                "note": "Bellissimo weekend nella capitale!",
                "dataCreazione": datetime(2025, 2, 1)
            },
            {
                "titolo": "Parigi in Primavera",
                "destinazione": "Parigi, Francia",
                "periodo": {"dataInizio": "2026-04-10", "dataFine": "2026-04-14"},
                "stato": "futuro",
                "location": {"lat": 48.8566, "lng": 2.3522},
                "creatore": c_anna,
                "partecipanti": [p_mario],
                "attivita": [
                    {"titolo": "Tour Eiffel", "tipo": "visita", "descrizione": "Salita sulla Torre Eiffel", "luogo": "Tour Eiffel"},
                    {"titolo": "Museo del Louvre", "tipo": "visita", "descrizione": "Visita al museo", "luogo": "Louvre"},
                    {"titolo": "Crociera sulla Senna", "tipo": "altro", "descrizione": "Crociera serale", "luogo": "Senna"}
                ],
                "spese": [
                    {"descrizione": "Volo A/R", "categoria": "trasporto", "importo": 180.0, "valuta": "EUR", "pagatore": {"id": "anna.verdi", "nome": "Anna Verdi"}},
                    {"descrizione": "Airbnb 4 notti", "categoria": "alloggio", "importo": 420.0, "valuta": "EUR", "pagatore": {"id": "mario.rossi", "nome": "Mario Rossi"}}
                ],
                "note": "Viaggio romantico a Parigi",
                "dataCreazione": datetime(2026, 1, 15)
            },
            {
                "titolo": "Trekking sulle Dolomiti",
                "destinazione": "Dolomiti, Italia",
                "periodo": {"dataInizio": "2026-07-01", "dataFine": "2026-07-05"},
                "stato": "futuro",
                "location": {"lat": 46.4102, "lng": 11.8440},
                "creatore": c_luca,
                "partecipanti": [p_mario, p_anna],
                "attivita": [
                    {"titolo": "Trekking Tre Cime di Lavaredo", "tipo": "visita", "descrizione": "Escursione panoramica", "luogo": "Tre Cime"},
                    {"titolo": "Rifugio Auronzo", "tipo": "pasto", "descrizione": "Pranzo al rifugio", "luogo": "Rifugio Auronzo"}
                ],
                "spese": [
                    {"descrizione": "Noleggio attrezzatura", "categoria": "attivita", "importo": 120.0, "valuta": "EUR", "pagatore": {"id": "luca.bianchi", "nome": "Luca Bianchi"}}
                ],
                "note": "Portare scarponi da montagna",
                "dataCreazione": datetime(2026, 2, 20)
            },
            {
                "titolo": "Barcellona e la Sagrada Familia",
                "destinazione": "Barcellona, Spagna",
                "periodo": {"dataInizio": "2025-06-20", "dataFine": "2025-06-24"},
                "stato": "concluso",
                "location": {"lat": 41.3851, "lng": 2.1734},
                "creatore": c_mario,
                "partecipanti": [p_anna],
                "attivita": [
                    {"titolo": "Sagrada Familia", "tipo": "visita", "descrizione": "Visita guidata alla basilica", "luogo": "Sagrada Familia"},
                    {"titolo": "Paella sulla Barceloneta", "tipo": "pasto", "descrizione": "Pranzo in riva al mare", "luogo": "Barceloneta"},
                    {"titolo": "Park Guell", "tipo": "visita", "descrizione": "Passeggiata nel parco di Gaudi", "luogo": "Park Guell"}
                ],
                "spese": [
                    {"descrizione": "Volo Ryanair", "categoria": "trasporto", "importo": 75.0, "valuta": "EUR", "pagatore": {"id": "mario.rossi", "nome": "Mario Rossi"}},
                    {"descrizione": "Ostello 4 notti", "categoria": "alloggio", "importo": 200.0, "valuta": "EUR", "pagatore": {"id": "anna.verdi", "nome": "Anna Verdi"}},
                    {"descrizione": "Biglietto Sagrada Familia", "categoria": "attivita", "importo": 52.0, "valuta": "EUR", "pagatore": {"id": "mario.rossi", "nome": "Mario Rossi"}}
                ],
                "note": "Gaudi e tapas!",
                "dataCreazione": datetime(2025, 5, 1)
            },
            {
                "titolo": "Londra Culturale",
                "destinazione": "Londra, Regno Unito",
                "periodo": {"dataInizio": "2026-09-05", "dataFine": "2026-09-08"},
                "stato": "futuro",
                "location": {"lat": 51.5074, "lng": -0.1278},
                "creatore": c_anna,
                "partecipanti": [p_luca],
                "attivita": [
                    {"titolo": "British Museum", "tipo": "visita", "descrizione": "Visita al museo gratuito", "luogo": "British Museum"},
                    {"titolo": "Musical nel West End", "tipo": "altro", "descrizione": "Spettacolo serale", "luogo": "West End"}
                ],
                "spese": [
                    {"descrizione": "Eurostar", "categoria": "trasporto", "importo": 130.0, "valuta": "EUR", "pagatore": {"id": "anna.verdi", "nome": "Anna Verdi"}},
                    {"descrizione": "Hotel zona Camden", "categoria": "alloggio", "importo": 350.0, "valuta": "EUR", "pagatore": {"id": "luca.bianchi", "nome": "Luca Bianchi"}}
                ],
                "note": "Ricordarsi l'ombrello!",
                "dataCreazione": datetime(2026, 3, 1)
            },
            {
                "titolo": "Firenze e gli Uffizi",
                "destinazione": "Firenze, Italia",
                "periodo": {"dataInizio": "2025-10-10", "dataFine": "2025-10-12"},
                "stato": "concluso",
                "location": {"lat": 43.7696, "lng": 11.2558},
                "creatore": c_luca,
                "partecipanti": [p_mario, p_anna],
                "attivita": [
                    {"titolo": "Galleria degli Uffizi", "tipo": "visita", "descrizione": "Capolavori del Rinascimento", "luogo": "Uffizi"},
                    {"titolo": "Bistecca alla Fiorentina", "tipo": "pasto", "descrizione": "Cena tipica toscana", "luogo": "Trattoria ZaZa"}
                ],
                "spese": [
                    {"descrizione": "Treno Frecciarossa", "categoria": "trasporto", "importo": 90.0, "valuta": "EUR", "pagatore": {"id": "luca.bianchi", "nome": "Luca Bianchi"}},
                    {"descrizione": "B&B centro", "categoria": "alloggio", "importo": 180.0, "valuta": "EUR", "pagatore": {"id": "mario.rossi", "nome": "Mario Rossi"}},
                    {"descrizione": "Cena tipica", "categoria": "cibo", "importo": 120.0, "valuta": "EUR", "pagatore": {"id": "anna.verdi", "nome": "Anna Verdi"}}
                ],
                "note": "Arte e buon cibo!",
                "dataCreazione": datetime(2025, 9, 1)
            },
            {
                "titolo": "Avventura in Islanda",
                "destinazione": "Reykjavik, Islanda",
                "periodo": {"dataInizio": "2026-08-15", "dataFine": "2026-08-22"},
                "stato": "futuro",
                "location": {"lat": 64.1466, "lng": -21.9426},
                "creatore": c_mario,
                "partecipanti": [p_anna, p_luca],
                "attivita": [
                    {"titolo": "Golden Circle Tour", "tipo": "visita", "descrizione": "Geysir, Gullfoss e Thingvellir", "luogo": "Golden Circle"},
                    {"titolo": "Blue Lagoon", "tipo": "altro", "descrizione": "Bagno termale geotermico", "luogo": "Blue Lagoon"},
                    {"titolo": "Whale Watching", "tipo": "altro", "descrizione": "Avvistamento balene", "luogo": "Husavik"}
                ],
                "spese": [
                    {"descrizione": "Volo diretto", "categoria": "trasporto", "importo": 320.0, "valuta": "EUR", "pagatore": {"id": "mario.rossi", "nome": "Mario Rossi"}},
                    {"descrizione": "Camper 7 giorni", "categoria": "alloggio", "importo": 890.0, "valuta": "EUR", "pagatore": {"id": "anna.verdi", "nome": "Anna Verdi"}},
                    {"descrizione": "Blue Lagoon ingresso", "categoria": "attivita", "importo": 75.0, "valuta": "EUR", "pagatore": {"id": "luca.bianchi", "nome": "Luca Bianchi"}}
                ],
                "note": "Portare vestiti caldi!",
                "dataCreazione": datetime(2026, 1, 10)
            },
            {
                "titolo": "Tour della Sicilia",
                "destinazione": "Sicilia, Italia",
                "periodo": {"dataInizio": "2025-08-01", "dataFine": "2025-08-08"},
                "stato": "concluso",
                "location": {"lat": 37.5079, "lng": 15.0830},
                "creatore": c_anna,
                "partecipanti": [p_mario, p_luca],
                "attivita": [
                    {"titolo": "Valle dei Templi", "tipo": "visita", "descrizione": "Templi greci ad Agrigento", "luogo": "Agrigento"},
                    {"titolo": "Escursione sull'Etna", "tipo": "visita", "descrizione": "Salita sul vulcano", "luogo": "Etna"},
                    {"titolo": "Granita e brioche", "tipo": "pasto", "descrizione": "Colazione siciliana tipica", "luogo": "Taormina"}
                ],
                "spese": [
                    {"descrizione": "Noleggio auto", "categoria": "trasporto", "importo": 350.0, "valuta": "EUR", "pagatore": {"id": "anna.verdi", "nome": "Anna Verdi"}},
                    {"descrizione": "Agriturismi vari", "categoria": "alloggio", "importo": 560.0, "valuta": "EUR", "pagatore": {"id": "mario.rossi", "nome": "Mario Rossi"}},
                    {"descrizione": "Cibo e ristoranti", "categoria": "cibo", "importo": 280.0, "valuta": "EUR", "pagatore": {"id": "luca.bianchi", "nome": "Luca Bianchi"}},
                    {"descrizione": "Guida Etna", "categoria": "attivita", "importo": 60.0, "valuta": "EUR", "pagatore": {"id": "anna.verdi", "nome": "Anna Verdi"}}
                ],
                "note": "La Sicilia e' meravigliosa!",
                "dataCreazione": datetime(2025, 6, 15)
            },
            {
                "titolo": "Amsterdam Art Tour",
                "destinazione": "Amsterdam, Paesi Bassi",
                "periodo": {"dataInizio": "2026-05-20", "dataFine": "2026-05-23"},
                "stato": "futuro",
                "location": {"lat": 52.3676, "lng": 4.9041},
                "creatore": c_luca,
                "partecipanti": [p_mario],
                "attivita": [
                    {"titolo": "Van Gogh Museum", "tipo": "visita", "descrizione": "Collezione Van Gogh", "luogo": "Van Gogh Museum"},
                    {"titolo": "Giro in bicicletta", "tipo": "altro", "descrizione": "Tour della citta in bici", "luogo": "Amsterdam centro"}
                ],
                "spese": [
                    {"descrizione": "Volo low cost", "categoria": "trasporto", "importo": 95.0, "valuta": "EUR", "pagatore": {"id": "luca.bianchi", "nome": "Luca Bianchi"}},
                    {"descrizione": "Houseboat 3 notti", "categoria": "alloggio", "importo": 300.0, "valuta": "EUR", "pagatore": {"id": "mario.rossi", "nome": "Mario Rossi"}}
                ],
                "note": "Noleggiare bici all'arrivo",
                "dataCreazione": datetime(2026, 2, 1)
            },
            {
                "titolo": "Costiera Amalfitana",
                "destinazione": "Costiera Amalfitana, Italia",
                "periodo": {"dataInizio": "2025-09-12", "dataFine": "2025-09-15"},
                "stato": "concluso",
                "location": {"lat": 40.6333, "lng": 14.6029},
                "creatore": c_mario,
                "partecipanti": [p_anna, p_luca],
                "attivita": [
                    {"titolo": "Sentiero degli Dei", "tipo": "visita", "descrizione": "Trekking panoramico sulla costiera", "luogo": "Sentiero degli Dei"},
                    {"titolo": "Gita in barca a Capri", "tipo": "altro", "descrizione": "Escursione in barca", "luogo": "Capri"},
                    {"titolo": "Cena vista mare", "tipo": "pasto", "descrizione": "Ristorante panoramico", "luogo": "Positano"}
                ],
                "spese": [
                    {"descrizione": "Auto a noleggio", "categoria": "trasporto", "importo": 150.0, "valuta": "EUR", "pagatore": {"id": "mario.rossi", "nome": "Mario Rossi"}},
                    {"descrizione": "Hotel Amalfi", "categoria": "alloggio", "importo": 450.0, "valuta": "EUR", "pagatore": {"id": "anna.verdi", "nome": "Anna Verdi"}},
                    {"descrizione": "Barca per Capri", "categoria": "trasporto", "importo": 80.0, "valuta": "EUR", "pagatore": {"id": "luca.bianchi", "nome": "Luca Bianchi"}},
                    {"descrizione": "Limoncello artigianale", "categoria": "shopping", "importo": 25.0, "valuta": "EUR", "pagatore": {"id": "mario.rossi", "nome": "Mario Rossi"}}
                ],
                "note": "Panorami mozzafiato!",
                "dataCreazione": datetime(2025, 8, 1)
            }
        ]

        collection.insert_many(viaggi_seed)
        print(f"{len(viaggi_seed)} viaggi inseriti")
    else:
        print(f"Database gia' popolato: {collection.count_documents({})} viaggi, {utenti_collection.count_documents({})} utenti")


# Entry point per esecuzione diretta
if __name__ == "__main__":
    seed_database()
    app.run(host="0.0.0.0", port=8000, debug=True)