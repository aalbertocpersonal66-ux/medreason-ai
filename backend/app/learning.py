from datetime import date, timedelta
from uuid import uuid4

# Baraja inicial ampliada: contenidos del ciclo clínico y del caso de dolor torácico.
FLASHCARDS = [
 {"id":"fc-001","front":"¿Qué mecanismo suele iniciar un IAM tipo 1?","back":"Rotura o erosión de placa aterosclerótica con trombosis coronaria.","tags":["cardiologia","fisiopatologia"],"level":"clinical"},
 {"id":"fc-002","front":"¿Debe esperarse la troponina ante un IAMCEST diagnóstico?","back":"No. La reperfusión no debe retrasarse esperando biomarcadores.","tags":["cardiologia","terapeutica"],"level":"clinical"},
 {"id":"fc-003","front":"¿Qué significa sensibilidad de una prueba?","back":"Proporción de enfermos con resultado positivo.","tags":["basico","epidemiologia"],"level":"basic"},
 {"id":"fc-004","front":"¿Qué territorio sugieren ST elevado en V1-V4?","back":"Infarto anterior o anteroseptal; suele implicar la descendente anterior.","tags":["cardiologia","ecg"],"level":"clinical"},
 {"id":"fc-005","front":"¿Cuál es el síntoma típico del dolor isquémico?","back":"Opresión retroesternal, a menudo desencadenada por esfuerzo.","tags":["cardiologia","semiologia"],"level":"basic"},
 {"id":"fc-006","front":"¿A dónde puede irradiar el dolor de un IAM?","back":"Brazo, hombro, cuello, mandíbula o espalda.","tags":["cardiologia","semiologia"],"level":"basic"},
 {"id":"fc-007","front":"¿Qué síntomas vegetativos acompañan al IAM?","back":"Diaforesis, náuseas y vómitos.","tags":["cardiologia","semiologia"],"level":"basic"},
 {"id":"fc-008","front":"¿Qué biomarcador se utiliza para lesión miocárdica?","back":"Troponina cardíaca I o T, interpretada en serie y contexto clínico.","tags":["cardiologia","laboratorio"],"level":"clinical"},
 {"id":"fc-009","front":"¿Qué demuestra una troponina elevada?","back":"Lesión miocárdica; no identifica por sí sola la causa.","tags":["cardiologia","laboratorio"],"level":"clinical"},
 {"id":"fc-010","front":"¿Qué hacer ante sospecha de síndrome coronario agudo?","back":"Evaluación inmediata, ECG precoz, monitorización y estratificación de riesgo.","tags":["urgencias","cardiologia"],"level":"clinical"},
 {"id":"fc-011","front":"¿En cuánto tiempo debe obtenerse el ECG inicial?","back":"Dentro de los primeros 10 minutos del primer contacto médico.","tags":["urgencias","ecg"],"level":"clinical"},
 {"id":"fc-012","front":"¿Qué significa elevación persistente del ST en contexto compatible?","back":"Sugiere oclusión coronaria aguda y exige estrategia urgente de reperfusión.","tags":["cardiologia","ecg"],"level":"clinical"},
 {"id":"fc-013","front":"¿Cuál es el objetivo de la reperfusión en IAMCEST?","back":"Restablecer cuanto antes el flujo coronario y limitar el tamaño del infarto.","tags":["cardiologia","terapeutica"],"level":"clinical"},
 {"id":"fc-014","front":"¿Cuál es la estrategia de reperfusión preferida si está disponible a tiempo?","back":"Intervención coronaria percutánea primaria.","tags":["cardiologia","terapeutica"],"level":"clinical"},
 {"id":"fc-015","front":"¿Qué complicación eléctrica puede aparecer precozmente en un IAM?","back":"Taquicardia o fibrilación ventricular, entre otras arritmias.","tags":["cardiologia","complicaciones"],"level":"clinical"},
 {"id":"fc-016","front":"¿Qué complicación hemodinámica grave puede causar un IAM extenso?","back":"Insuficiencia cardíaca aguda y shock cardiogénico.","tags":["cardiologia","complicaciones"],"level":"clinical"},
 {"id":"fc-017","front":"¿Qué factores de riesgo coronario modificables preguntar?","back":"Tabaquismo, hipertensión, diabetes, dislipidemia, dieta y sedentarismo.","tags":["prevencion","cardiologia"],"level":"basic"},
 {"id":"fc-018","front":"¿Cómo se calcula el índice paquetes-año?","back":"Paquetes fumados al día × años de consumo.","tags":["semiologia","tabaquismo"],"level":"basic"},
 {"id":"fc-019","front":"¿Qué caracteriza a la angina inestable?","back":"Isquemia miocárdica aguda sin evidencia de necrosis por biomarcadores.","tags":["cardiologia","diagnostico"],"level":"clinical"},
 {"id":"fc-020","front":"¿Qué diferencia IAM de lesión miocárdica aislada?","back":"IAM requiere lesión aguda más evidencia clínica de isquemia.","tags":["cardiologia","diagnostico"],"level":"clinical"},
 {"id":"fc-021","front":"¿Qué es la frecuencia cardíaca compensatoria en shock?","back":"Taquicardia por activación simpática para sostener el gasto cardíaco.","tags":["fisiopatologia","urgencias"],"level":"clinical"},
 {"id":"fc-022","front":"¿Qué representa la diaforesis en el IAM?","back":"Respuesta autonómica simpática asociada al dolor y al estrés isquémico.","tags":["fisiopatologia","semiologia"],"level":"clinical"},
 {"id":"fc-023","front":"¿Qué derivaciones exploran la pared anterior?","back":"V3-V4; V1-V2 exploran principalmente el septo.","tags":["ecg","cardiologia"],"level":"clinical"},
 {"id":"fc-024","front":"¿Qué derivaciones exploran la pared lateral alta?","back":"DI y aVL; V5-V6 exploran la pared lateral baja.","tags":["ecg","cardiologia"],"level":"clinical"},
 {"id":"fc-025","front":"¿Por qué repetir ECG si persiste el dolor?","back":"Los cambios isquémicos pueden evolucionar y el primer ECG puede ser no diagnóstico.","tags":["ecg","urgencias"],"level":"clinical"}
]

def review_sm2(card_state: dict, quality: int):
    """SM-2 simplificado. quality 0..5; persiste el estado devuelto en BD."""
    if quality not in range(6): raise ValueError("quality debe estar entre 0 y 5")
    reps=card_state.get("repetitions",0); interval=card_state.get("interval_days",0)
    ease=card_state.get("ease_factor",2.5)
    if quality < 3:
        reps, interval = 0, 1
    else:
        if reps == 0: interval=1
        elif reps == 1: interval=6
        else: interval=round(interval*ease)
        reps += 1
    ease=max(1.3, ease + (0.1-(5-quality)*(0.08+(5-quality)*0.02)))
    due=date.today()+timedelta(days=interval)
    return {"repetitions":reps,"interval_days":interval,"ease_factor":round(ease,2),"due_date":due.isoformat()}

def make_flashcard(front: str, back: str, tags=None):
    return {"id":str(uuid4()),"front":front,"back":back,"tags":tags or [],"level":"custom"}
