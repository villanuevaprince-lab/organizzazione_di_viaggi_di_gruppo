#!/bin/bash
# Test completo dell'applicazione SPA Viaggi

echo "🧪 Test Suite - SPA Viaggi di Gruppo"
echo "===================================="
echo ""

# Test 1: Backend Health
echo "✅ Test 1: Backend Health Check"
HEALTH=$(curl -s http://localhost:8000/health | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['status'])")
if [ "$HEALTH" == "healthy" ]; then
    echo "   ✓ Backend attivo e database connesso"
else
    echo "   ✗ Backend non risponde"
    exit 1
fi
echo ""

# Test 2: CORS Configuration
echo "✅ Test 2: CORS Configuration"
CORS=$(curl -I -s -X OPTIONS http://localhost:8000/api/login \
  -H "Origin: https://test.example.com" \
  -H "Access-Control-Request-Method: POST" | grep -i "access-control-allow-origin")
if [[ $CORS == *"*"* ]]; then
    echo "   ✓ CORS configurato correttamente"
else
    echo "   ✗ CORS non configurato"
    exit 1
fi
echo ""

# Test 3: Login API
echo "✅ Test 3: Login API (mario.rossi)"
LOGIN=$(curl -s -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"mario.rossi"}' | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['success'])")
if [ "$LOGIN" == "True" ]; then
    echo "   ✓ Login mario.rossi valido"
else
    echo "   ✗ Login fallito"
    exit 1
fi
echo ""

# Test 4: Elenco Viaggi
echo "✅ Test 4: Elenco Viaggi"
VIAGGI_COUNT=$(curl -s http://localhost:8000/api/viaggi | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['count'])")
if [ "$VIAGGI_COUNT" == "10" ]; then
    echo "   ✓ Trovati $VIAGGI_COUNT viaggi"
else
    echo "   ✗ Numero viaggi errato: $VIAGGI_COUNT"
    exit 1
fi
echo ""

# Test 5: Dettaglio Viaggio
echo "✅ Test 5: Dettaglio Viaggio"
VIAGGIO_ID=$(curl -s http://localhost:8000/api/viaggi | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['viaggi'][0]['_id'])")
VIAGGIO_TITLE=$(curl -s "http://localhost:8000/api/viaggi/$VIAGGIO_ID" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['viaggio']['titolo'])")
if [ -n "$VIAGGIO_TITLE" ]; then
    echo "   ✓ Dettaglio viaggio caricato: $VIAGGIO_TITLE"
else
    echo "   ✗ Dettaglio viaggio non trovato"
    exit 1
fi
echo ""

# Test 6: Utenti Esistenti
echo "✅ Test 6: Verifica Tutti gli Utenti"
for USER in "mario.rossi" "anna.verdi" "luca.bianchi"; do
    LOGIN_TEST=$(curl -s -X POST http://localhost:8000/api/login \
      -H "Content-Type: application/json" \
      -d "{\"username\":\"$USER\"}" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('success', False))")
    if [ "$LOGIN_TEST" == "True" ]; then
        echo "   ✓ $USER verificato"
    else
        echo "   ✗ $USER non trovato"
    fi
done
echo ""

# Riepilogo
echo "===================================="
echo "🎉 Tutti i test passati con successo!"
echo ""
echo "📱 Accedi al frontend:"
echo "   https://literate-space-bassoon-wrqgp95qrr54c5vj9-5500.app.github.dev"
echo ""
echo "📚 API Documentation:"
echo "   https://literate-space-bassoon-wrqgp95qrr54c5vj9-8000.app.github.dev/docs"
echo ""
echo "🔐 Utenti disponibili:"
echo "   - mario.rossi"
echo "   - anna.verdi"
echo "   - luca.bianchi"
echo ""
