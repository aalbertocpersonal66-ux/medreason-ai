"""Paciente virtual determinístico: responde con datos del guion, sin inventar información."""
import re
import unicodedata

# Cada grupo reúne formulaciones habituales de una misma pregunta clínica.
# La normalización permite reconocer preguntas con o sin tildes y signos.
FACTS = [
    ("inicio", ("cuando comenzo", "desde cuando", "hace cuanto", "a que hora", "inicio", "empezo", "tiempo de evolucion", "cuanto tiempo lleva"),
     "Comenzó hace aproximadamente una hora."),
    ("localizacion", ("donde", "en que parte", "en que lugar", "localiza", "sitio del dolor", "ubicacion"),
     "Lo siento en el centro del pecho, detrás del esternón."),
    ("caracter", ("como es", "que tipo de dolor", "como describiria", "que siente", "sensacion", "opresivo", "presion", "aplast"),
     "Es una presión muy fuerte, como si algo me aplastara."),
    ("irradiacion", ("se corre", "se extiende", "hacia donde", "irradia", "brazo", "mandibula", "espalda", "cuello"),
     "Se extiende hacia el brazo izquierdo y la mandíbula."),
    ("intensidad", ("cuanto duele", "que intensidad", "escala", "del uno al diez", "de 0 a 10", "dolor de cero", "fuerte es"),
     "Diría que es un ocho sobre diez."),
    ("acompanantes", ("otros sintomas", "algo mas", "ademas del dolor", "acompanado", "nausea", "vomito", "sudor", "transpir", "falta de aire", "mareo"),
     "Estoy sudando frío y tengo náuseas."),
    ("antecedentes", ("antecedentes", "enfermedades", "padece", "sufre", "hipertension", "presion alta", "diabetes", "problemas cardiacos", "enfermo"),
     "Tengo hipertensión."),
    ("medicacion", ("medicamento", "medicacion", "que toma", "toma algun", "tratamiento habitual", "enalapril", "pastillas", "farmaco"),
     "Tomo enalapril para la presión."),
    ("tabaco", ("fuma", "fumador", "tabaco", "cigarrillo", "paquetes", "dejo de fumar"),
     "Fumo desde hace años, aproximadamente un paquete al día."),
]

def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFD", value.lower())
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def respond(question: str) -> dict:
    q = _normalize(question)
    found = []
    for key, phrases, answer in FACTS:
        if any(re.search(r"(?<![a-z0-9])" + re.escape(_normalize(phrase)) + r"(?![a-z0-9])", q) for phrase in phrases):
            found.append((key, answer))

    if not found:
        return {
            "answer": "No recuerdo ese dato con claridad. ¿Podría preguntarme por el inicio, la ubicación, las características, la intensidad, los síntomas acompañantes, mis antecedentes, mis medicamentos o el consumo de tabaco?",
            "facts_retrieved": [],
            "grounded": True
        }

    return {
        "answer": " ".join(answer for _, answer in found),
        "facts_retrieved": [key for key, _ in found],
        "grounded": True
    }
