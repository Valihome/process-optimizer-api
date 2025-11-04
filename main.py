from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json # Adaugat pentru parsarea raspunsului AI
from google import genai
from google.genai import types

# Variabila OBLIGATORIE 'app' pentru Gunicorn și Flask
app = Flask(__name__)
# Permite accesul din Frontend. Atentie: Nu lasa spatii invizibile dupa CORS(app)
CORS(app) 

# --- 1. CONFIGURARE GEMINI API ---
try:
    # Clientul se va initializa daca variabila de mediu GEMINI_API_KEY este setata
    client = genai.Client()
except Exception as e:
    # Atentie: Initializarea clientului AI a esuat
    print(f"Atentie: Initializarea clientului AI a esuat. S-a asteapta setarea GEMINI_API_KEY. Eroare: {e}")
    client = None

# Definirea schemei de răspuns JSON
RESPONSE_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "analiza_generala": types.Schema(type=types.Type.STRING, description="Un rezumat general al procesului, incluzând domeniul selectat și numărul de probleme identificate. Foloseste **bold**."),
        "oportunitati_optimizare": types.Schema(
            type=types.Type.ARRAY,
            description="O lista cu minim 2-3 pasi care pot fi automatizati.",
            items=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "pas_proces_original": types.Schema(type=types.Type.STRING, description="Descrierea exacta a pasului original din textul utilizatorului."),
                    "tip_ineficienta": types.Schema(type=types.Type.STRING, description="Ex: Repetitiv, Risc de Eroare, Blocaj, Timp de Asteptare. Foloseste **bold**."),
                    "impact_estimat": types.Schema(type=types.Type.STRING, description="Ex: Economie de 3 ore/saptamana, Reducerea erorilor cu 80%. Foloseste **bold**."),
                    "solutie_recomandata": types.Schema(type=types.Type.STRING, description="Ex: Automatizare RPA, Low-Code Workflow, Integrare API. Foloseste **bold**."),
                    "instrument_sugerat": types.Schema(type=types.Type.STRING, description="Ex: UiPath, Zapier, Google Apps Script, Python. Foloseste **bold**."),
                    "prompt_cod_relevant": types.Schema(type=types.Type.STRING, description="Un prompt detaliat sau un snippet de cod relevant pentru solutie. Foloseste 'N/A' daca nu este necesar."),
                },
                required=["pas_proces_original", "tip_ineficienta", "impact_estimat", "solutie_recomandata", "instrument_sugerat", "prompt_cod_relevant"]
            )
        ),
        "next_steps": types.Schema(type=types.Type.STRING, description="Un paragraf scurt care incurajeaza utilizatorul sa treaca la implementare. Foloseste **bold**.")
    },
    required=["analiza_generala", "oportunitati_optimizare", "next_steps"]
)

# 2. Ruta API pentru analiză
@app.route('/api/analyze', methods=['POST'])
def analyze_process():
    data = request.get_json()
    domeniu = data.get('domeniu', 'General/Altele')
    description = data.get('description', 'Fara descriere')

    if not description:
        return jsonify({"error": "Descrierea procesului este goala."}), 400
    
    if client is None:
        # EROARE DE CONEXIUNE / SERVICE INDISPONIBIL
        return jsonify({"error": "Clientul AI nu a putut fi initializat. Verificati cheia GEMINI_API_KEY."}), 503

    # Instructiunile detaliate pentru modelul AI (Focus pe Expertiza)
    prompt = f"""
    Esti un expert de top in domeniul **automatizarii proceselor** specializat in **{domeniu}**. 
    Rolul tau este sa analizezi procesul descris de utilizator si sa oferi solutii bazate pe cea mai buna practica din industria **{domeniu}**. 
    
    Obiectivul este de a identifica pasii repetitivi, cu risc de eroare sau consumatori de timp, si de a oferi solutii structurate, instrumente sugerate si prompt-uri/cod relevante.

    Descrierea procesului de analizat: "{description}"

    Genereaza raspunsul strict in formatul JSON definit de schema de raspuns. Nu adauga niciun text explicativ inafara structurii JSON.
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=RESPONSE_SCHEMA,
            ),
        )

        # CORECȚIA CRITICĂ: Parsare și jsonify
        try:
            # 1. Transformă textul JSON în obiect Python (dict)
            json_response = json.loads(response.text)
        except json.JSONDecodeError:
            app.logger.error("AI a returnat un JSON invalid: %s", response.text)
            return jsonify({"error": "AI a returnat un format JSON invalid. Încercați din nou sau cu un prompt diferit."}), 500
            
        # 2. Folosește jsonify pentru a returna dict-ul ca răspuns HTTP JSON
        return jsonify(json_response), 200

    except Exception as e:
        app.logger.error(f"Eroare la apelarea Gemini API: {e}")
        return jsonify({"error": f"Eroare la procesarea cererii de AI: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
