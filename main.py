from flask import Flask, jsonify, request
from flask_cors import CORS 
import os 
from google import genai
from google.genai import types

# Variabila OBLIGATORIE 'app' pentru Gunicorn și Flask
app = Flask(__name__)
# Activează CORS pentru a permite Frontend-ului să acceseze API-ul
CORS(app) 

# --- 1. CONFIGURARE GEMINI API ---
# Clientul citește automat cheia din variabila de mediu GEMINI_API_KEY
try:
    client = genai.Client()
except Exception as e:
    # Dacă cheia nu este setată (înainte de deploy), acest lucru poate eșua inițializarea
    print(f"Atenție: Inițializarea clientului AI a eșuat. S-a așteaptă setarea GEMINI_API_KEY. Eroare: {e}")
    client = None

# Definirea schemei de răspuns JSON (Schema) pe care o dorim de la model
# Aceasta asigură că răspunsul se potrivește cu formatul așteptat de Frontend
RESPONSE_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "analiza_generala": types.Schema(type=types.Type.STRING, description="O frază sumară a procesului și a oportunităților generale."),
        "oportunitati_optimizare": types.Schema(
            type=types.Type.ARRAY,
            description="O listă cu minim 2-3 pași care pot fi automatizați.",
            items=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "pas_proces_original": types.Schema(type=types.Type.STRING, description="Descrierea exactă a pasului original din textul utilizatorului."),
                    "tip_ineficienta": types.Schema(type=types.Type.STRING, description="Ex: Repetitiv, Risc de Eroare, Blocaj, Timp de Așteptare."),
                    "impact_estimat": types.Schema(type=types.Type.STRING, description="Ex: Economie de 3 ore/săptămână, Reducerea erorilor cu 80%."),
                    "solutie_recomandata": types.Schema(type=types.Type.STRING, description="Ex: Automatizare RPA, Low-Code Workflow, Integrare API."),
                    "instrument_sugerat": types.Schema(type=types.Type.STRING, description="Ex: UiPath, Zapier, Google Apps Script, Python."),
                    "prompt_cod_relevant": types.Schema(type=types.Type.STRING, description="Un prompt detaliat sau un snippet de cod relevant pentru soluție. Folosește 'N/A' dacă nu este necesar."),
                },
                required=["pas_proces_original", "tip_ineficienta", "impact_estimat", "solutie_recomandata", "instrument_sugerat", "prompt_cod_relevant"]
            )
        ),
        "next_steps": types.Schema(type=types.Type.STRING, description="Un paragraf scurt care încurajează utilizatorul să treacă la implementare.")
    },
    required=["analiza_generala", "oportunitati_optimizare", "next_steps"]
)

# 2. Ruta API pentru analiză
@app.route('/api/analyze', methods=['POST'])
def analyze_process():
    # Preluarea datelor din cererea JSON trimisă de Frontend
    data = request.get_json()
    domeniu = data.get('domeniu', 'General')
    description = data.get('description', 'Fără descriere')

    if not description:
        return jsonify({"error": "Descrierea procesului este goală."}), 400
    
    if client is None:
        return jsonify({"error": "Clientul AI nu a putut fi inițializat. Verificați cheia GEMINI_API_KEY."}), 503

    # Instrucțiunile detaliate pentru modelul AI
    prompt = f"""
    Ești un expert în automatizare. Analizează procesul descris mai jos, ținând cont că domeniul de activitate este {domeniu}. 
    Obiectivul este de a identifica pașii repetitivi, cu risc de eroare sau consumatori de timp, și de a oferi soluții structurate.

    Descrierea procesului: "{description}"

    Generează răspunsul strict în formatul JSON definit de schema de răspuns. Nu adăuga niciun text explicativ înafara structurii JSON.
    """

    try:
        # Apelarea modelului Gemini cu schema de răspuns (Response Schema)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=RESPONSE_SCHEMA,
            ),
        )

        # Răspunsul este deja un string JSON valid, îl returnăm direct
        return response.text, 200, {'Content-Type': 'application/json'}

    except Exception as e:
        # Tratează erorile de API
        app.logger.error(f"Eroare la apelarea Gemini API: {e}")
        return jsonify({"error": f"Eroare la procesarea cererii de AI (Verifică log-urile Render): {str(e)}"}), 500

if __name__ == '__main__':
    # Folosește un port specificat de Render sau 5000 local
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
