"""Paciente virtual determinístico: revela únicamente hechos del guion autorizado."""
FACTS = {
    "inicio": (["cuando", "comenzo", "empezo", "inicio", "tiempo"], "Comenzó hace aproximadamente una hora."),
    "localizacion": (["donde", "localiza", "lugar", "sitio"], "Lo siento en el centro del pecho, detrás del esternón."),
    "caracter": (["como es", "tipo", "caracter", "sensacion"], "Es una presión muy fuerte, como si algo me aplastara."),
    "irradiacion": (["irradia", "extiende", "brazo", "mandibula"], "Se extiende hacia el brazo izquierdo y la mandíbula."),
    "intensidad": (["intensidad", "fuerte", "escala", "cuanto duele"], "Diría que es un ocho sobre diez."),
    "acompanantes": (["otros sintomas", "acompaña", "nausea", "sudor", "sintomas"], "Estoy sudando frío y tengo náuseas."),
    "antecedentes": (["antecedentes", "enfermedades", "hipertension", "presion"], "Tengo hipertensión."),
    "medicacion": (["medicacion", "medicamentos", "toma", "enalapril"], "Tomo enalapril para la presión."),
    "tabaco": (["fuma", "tabaco", "cigarrillo"], "Fumo desde hace años, aproximadamente un paquete al día.")
}

def respond(question: str) -> dict:
    q=question.lower()
    for a,b in (("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ñ","n")):
        q=q.replace(a,b)
    found=[]
    for key,(terms,answer) in FACTS.items():
        if any(term in q for term in terms): found.append((key,answer))
    if not found:
        return {"answer":"No estoy seguro de haber entendido. ¿Podría preguntarme de otra manera?","facts_retrieved":[],"grounded":True}
    return {"answer":" ".join(answer for _,answer in found),"facts_retrieved":[key for key,_ in found],"grounded":True}
