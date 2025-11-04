import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from google.genai import types

# ----------------------------------------------------
# 1. Configurarea Aplicatiei si API Key
# ----------------------------------------------------
app = Flask(__name__)
# Permite cererile CORS de pe orice domeniu (Frontend-ul tau Render)
CORS(app) 

# Initializarea clientului Gemini
try:
    # GenAI citeste automat GEMINI_API_KEY din variabilele de mediu Render
    client = genai.Client()
except Exception as e:
    print(f"Eroare la initializarea clientului Gemini: {e}")
    client = None

# ----------------------------------------------------
# 2. Schema de Raspuns (CRITICA PENTRU VALIDARE JSON)
# ----------------------------------------------------
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

# ----------------------------------------------------
# 3. Prompt si Functie de Analiza
# ----------------------------------------------------
SYSTEM_INSTRUCTION = (
    "Ești un expert în automatizarea proceselor de afaceri (BPA) și în eficientizare digitală. "
    "Misiunea ta este să analizezi un proces descris de utilizator, să identifici punctele de ineficiență (repetiții, blocaje, riscuri de eroare) și să propui soluții concrete de automatizare, folosind instrumente relevante. "
    "Răspunsul tău trebuie să fie strict în limba română și să respecte formatul JSON specificat exact, fără text explicativ suplimentar."
)

def generate_analysis(domeniu, description):
    # Modelul ideal pentru extragerea JSON structurat
    model = 'gemini-2.5-flash'

    prompt_text = (
        f"Analizează următorul proces din domeniul '{domeniu}'. "
        f"Procesul: '{description}'. "
        "Identifică minim 3 oportunități clare de automatizare sau optimizare și completează strict schema JSON."
    )

    try:
        response = client.models.generate_content(
            model=model,
            contents=[prompt_text],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=RESPONSE_SCHEMA,
                temperature=0.2 
            )
        )
        # Conținutul va fi un string JSON
        return response.text
    except Exception as e:
        app.logger.error(f"Eroare la apelarea Gemini API: {e}")
        return None

# ----------------------------------------------------
# 4. Rute Flask
# ----------------------------------------------------
@app.route('/api/analyze', methods=['POST'])
def analyze_process():
    if client is None:
        return jsonify({"error": "Serviciul Gemini nu este configurat sau API Key lipsește."}), 500

    data = request.get_json()
    domeniu = data.get('domeniu')
    description = data.get('description')

    if not domeniu or not description:
        return jsonify({"error": "Domeniul și descrierea procesului sunt obligatorii."}), 400

    try:
        json_output = generate_analysis(domeniu, description)

        if json_output is None:
            # Daca generate_analysis returneaza None, este o eroare interna Gemini
            return jsonify({"error": "Generarea analizei a eșuat. Vă rugăm reîncercați."}), 500

        # Returneaza direct string-ul JSON generat de model
        return app.response_class(
            response=json_output,
            status=200,
            mimetype='application/json'
        )

    except Exception as e:
        app.logger.error(f"Eroare neașteptată în ruta /api/analyze: {e}")
        return jsonify({"error": f"Eroare de server neașteptată: {e}"}), 500

@app.route('/', methods=['GET'])
def home():
    # O simpla ruta de verificare pentru a confirma ca serverul ruleaza
    return jsonify({"status": "API is running", "service": "Process Optimizer Backend"})

# ----------------------------------------------------
# 5. Rulare Aplicatie
# ----------------------------------------------------
if __name__ == '__main__':
    # Ruleaza aplicatia direct, Render va folosi Gunicorn
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
