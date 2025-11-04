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
    # Daca API key-ul lipseste, clientul va fi None, iar eroarea va fi gestionata in ruta /api/analyze
    print(f"Eroare la initializarea clientului Gemini: {e}")
    client = None

# ----------------------------------------------------
# 2. Schema de Raspuns (CRITICA PENTRU VALIDARE JSON)
# Am separat proprietatile pentru a evita SyntaxError-ul la nesting.
# ----------------------------------------------------

# Definirea proprietatilor pentru un singur element (Oportunitate)
OPPORTUNITY_PROPERTIES = {
    "pas_proces_original": types.Schema(type=types.Type.STRING, description="Descrierea exacta a pasului original din textul utilizatorului."),
    "tip_ineficienta": types.Schema(type=types.Type.STRING, description="Ex: Repetitiv, Risc de Eroare, Blocaj, Timp de Asteptare. Foloseste **bold**."),
    "impact_estimat": types.Schema(type=types.Type.STRING, description="Ex: Economie de 3 ore/saptamana, Reducerea erorilor cu 80%. Foloseste **bold**."),
    "solutie_recomandata": types.Schema(type=types.Type.STRING, description="Ex: Automatizare RPA, Low-Code Workflow, Integrare API. Foloseste **bold**."),
    "instrument_sugerat": types.Schema(type=types.Type.STRING, description="Ex: UiPath, Zapier, Google Apps Script, Python. Foloseste **bold**."),
    "prompt_cod_relevant": types.Schema(type=types.Type.STRING, description="Un prompt detaliat sau un snippet de cod relevant pentru solutie. Foloseste 'N/A' daca nu este necesar."),
}

RESPONSE_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "analiza_generala": types.Schema(type=types.Type.STRING, description="Un rezumat general al procesului, incluzând domeniul selectat și numărul de probleme identificate. Foloseste **bold**."),
        "oportunitati_optimizare": types.Schema(
            type=types.Type.ARRAY,
            description="O lista cu minim 2-3 pasi care pot fi automatizati.",
            items=types.Schema(
                type=types.Type.OBJECT,
                properties=OPPORTUNITY_PROPERTIES,
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
    "Răspunsul tău trebuie să fie strict în limba română și să respecte formatul JSON
