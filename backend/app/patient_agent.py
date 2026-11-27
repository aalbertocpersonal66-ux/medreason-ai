"""Paciente virtual con memoria conversacional y respuestas limitadas al guion clínico."""
import re
import unicodedata
from typing import Any

def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFD", str(value).lower())
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()

# Intenciones clínicas y formulaciones frecuentes. Una pregunta puede activar varias.
INTENTS = {
    "onset": (("cuando", "desde cuando", "hace cuanto", "cuanto tiempo", "inicio", "empezo", "comenzo", "duracion", "hace cuanto tiempo"),),
    "location": (("donde", "en que parte", "en que lugar", "localizacion", "ubicacion", "sitio"),),
    "character": (("como es", "que tipo", "describa", "describir", "caracter", "sensacion", "opresivo", "punzante", "quemante", "presion"),),
    "radiation": (("irradia", "se extiende", "se corre", "hacia donde", "brazo", "mandibula", "cuello", "espalda"),),
    "severity": (("cuanto duele", "intensidad", "escala", "del uno al diez", "de 0 a 10", "del 1 al 10", "que tan fuerte", "tan intenso"),),
    "associated": (("otros sintomas", "sintomas asociados", "acompan", "ademas", "algo mas", "nausea", "vomito", "sudor", "transpir", "falta de aire", "disnea", "mareo"),),
    "history": (("antecedentes", "enfermedades", "padece", "sufre", "hipertension", "presion alta", "diabetes", "problemas cardiacos", "enfermedad previa"),),
    "medication": (("medicamento", "medicacion", "que toma", "toma algun", "tratamiento habitual", "enalapril", "pastillas", "farmaco"),),
    "smoking": (("fuma", "fumador", "tabaco", "cigarrillo", "paquetes ano", "paquetes al ano", "dejo de fumar"),),
}

def _contains(q: str, phrase: str) -> bool:
    phrase = _normalize(phrase)
    return bool(phrase) and re.search(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])", q) is not None

def _answer_for(intent: str, facts: dict[str, Any]) -> str | None:
    if intent == "onset":
        return f"Comenzó hace aproximadamente {facts['onset']}." if facts.get("onset") else None
    if intent == "location":
        return f"Lo siento en la región {facts['location']}." if facts.get("location") else None
    if intent == "character":
        return f"Es un dolor {facts['character']}." if facts.get("character") else None
    if intent == "radiation":
        return f"Se extiende hacia {facts['radiation']}." if facts.get("radiation") else None
    if intent == "severity":
        return f"La intensidad es de {facts['severity']}." if facts.get("severity") else None
    if intent == "associated":
        values = facts.get("associated") or []
        return f"Sí, tengo {', '.join(values)}." if values else None
    if intent == "history":
        values = facts.get("history") or []
        return f"Como antecedente, tengo {', '.join(values)}." if values else None
    if intent == "medication":
        values = facts.get("medication") or []
        return f"Actualmente tomo {', '.join(values)}." if values else None
    if intent == "smoking":
        value = facts.get("smoking")
        return f"Mi antecedente de tabaquismo es de {value}." if value else None
    return None

def respond(question: str, patient_script: dict | None = None, history: list | None = None) -> dict:
    """Responde usando solo hechos estructurados; history permite interpretar seguimientos."""
    script = patient_script or {
        "facts": {
            "onset": "60 minutos", "location": "retroesternal", "character": "opresivo",
            "radiation": "brazo izquierdo y mandíbula", "severity": "8/10",
            "associated": ["diaforesis", "náuseas"], "history": ["hipertensión"],
            "medication": ["enalapril"], "smoking": "20 paquetes-año"
        }
    }
    facts = script.get("facts", {})
    q = _normalize(question)
    matched = [name for name, groups in INTENTS.items()
               if any(_contains(q, phrase) for group in groups for phrase in group)]

    # Seguimientos breves: recupera el último tema preguntado si el usuario usa
    # expresiones anafóricas como "¿y eso?", "¿y cuál?" o "¿y actualmente?".
    if not matched and history and any(_contains(q, x) for x in
        ("y eso", "y cual", "y cuales", "y actualmente", "y antes", "y despues", "algo mas sobre eso")):
        for turn in reversed(history):
            previous = turn.get("facts_retrieved") or []
            if previous:
                matched = previous
                break

    answers = []
    retrieved = []
    for intent in matched:
        answer = _answer_for(intent, facts)
        if answer:
            answers.append(answer)
            retrieved.append(intent)

    if not answers:
        return {
            "answer": "No tengo ese dato en la historia que recuerdo. Puede preguntarme por el inicio, localización, tipo de dolor, irradiación, intensidad, síntomas acompañantes, antecedentes, medicamentos o tabaquismo.",
            "facts_retrieved": [],
            "grounded": True,
            "context_used": bool(history)
        }

    return {
        "answer": " ".join(answers),
        "facts_retrieved": retrieved,
        "grounded": True,
        "context_used": bool(history)
    }
