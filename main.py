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
