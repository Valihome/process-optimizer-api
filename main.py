from flask import Flask, jsonify, request
from flask_cors import CORS 

# Variabila OBLIGATORIE 'app' pentru Gunicorn
app = Flask(__name__)
CORS(app) 

# --- AICI VA FI INTEGRAREA AI-ULUI ÎN FAZA ULTERIOARĂ ---
MOCK_RESPONSE = {
    "analiza_generala": "Procesul a fost analizat. 3 puncte critice au fost identificate pentru automatizare imediată.",
    "oportunitati_optimizare": [
        {
            "pas_proces_original": "Preluarea manuală a datelor din sursa X.",
            "tip_ineficienta": "Repetitiv, Risc de Eroare",
            "impact_estimat": "Pierdere 4 ore/săptămână.",
            "solutie_recomandata": "Automatizare prin Webhook sau Integrare API.",
            "instrument_sugerat": "Zapier / Make",
            "prompt_cod_relevant": "Prompt Zapier: 'Setează un trigger pentru New Entry și folosește un formatter pentru a standardiza formatul datei.'"
        },
        {
            "pas_proces_original": "Aprobarea documentelor de către manager.",
            "tip_ineficienta": "Blocaj, Consumator de Timp",
            "impact_estimat": "Întârzieri de 24-48 de ore în ciclul de aprobare.",
            "solutie_recomandata": "Flow de aprobare automată bazat pe reguli (Low-Code).",
            "instrument_sugerat": "Microsoft Power Automate",
            "prompt_cod_relevant": "Cod Power Automate: 'IF valoare_factura < 1000 atunci aproba_automat ELSE trimite_la_manager.'"
        }
    ],
    "next_steps": "Contactați un specialist pentru a implementa prima automatizare în termen de o săptămână."
}

@app.route('/api/analyze', methods=['POST'])
def analyze_process():
    # Returnează răspunsul simulat
    return jsonify(MOCK_RESPONSE)
