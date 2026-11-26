from datetime import date, timedelta
from uuid import uuid4

FLASHCARDS = [
 {"id":"fc-001","front":"¿Qué mecanismo suele iniciar un IAM tipo 1?","back":"Rotura o erosión de placa aterosclerótica con trombosis coronaria.","tags":["cardiologia","fisiopatologia"],"level":"clinical"},
 {"id":"fc-002","front":"¿Debe esperarse la troponina si el ECG muestra IAMCEST diagnóstico?","back":"No. La reperfusión no debe retrasarse esperando biomarcadores.","tags":["cardiologia","terapeutica"],"level":"clinical"},
 {"id":"fc-003","front":"¿Qué significa sensibilidad de una prueba?","back":"Proporción de personas con la enfermedad que tienen resultado positivo.","tags":["basico","epidemiologia"],"level":"basic"}
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
