QUESTIONS = [
 "Defina el problema clínico principal en una frase.",
 "¿Cuáles son sus tres hipótesis prioritarias y qué dato apoya cada una?",
 "¿Qué dato cambiaría inmediatamente su conducta?",
 "Justifique el estudio que considera prioritario.",
 "Explique el mecanismo fisiopatológico que conecta los hallazgos.",
 "Describa su conducta inicial y las contraindicaciones que comprobaría.",
 "¿Qué complicaciones debe vigilar y cómo las reconocería?"
]

def oral_session(case_title: str):
    return {"case":case_title,"questions":QUESTIONS,"rubric_domains":[
      "claridad","priorización","integración de datos","justificación","seguridad"]}
