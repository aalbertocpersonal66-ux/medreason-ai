from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from pydantic import BaseModel, Field
from uuid import uuid4
from .patient_agent import respond
from .case_engine import load_case, STAGES, can_advance, stage_result
from .evaluator import Criterion, evaluate
from .learning import FLASHCARDS, review_sm2, make_flashcard
from .oral_exam import oral_session
from .metrics import summarize_attempts
from .planner import weekly_plan
from datetime import date
from docx import Document

app=FastAPI(title="MedReason AI API",version="0.2.0")
# Demo pública sin autenticación: no se envían cookies ni credenciales.
# En producción con usuarios, restringir origins y activar autenticación.
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=False,allow_methods=["*"],allow_headers=["*"])
attempts={}; card_states={}; custom_cards=[]

class Ask(BaseModel): attempt_id:str; question:str=Field(min_length=1,max_length=1500)
class Action(BaseModel): attempt_id:str; action_type:str; payload:dict={}
class Review(BaseModel): quality:int=Field(ge=0,le=5)
class PlanRequest(BaseModel): exam_date:date; hours_per_week:int=Field(ge=1,le=80); weaknesses:dict[str,float]
class CardCreate(BaseModel): front:str; back:str; tags:list[str]=[]

@app.get('/health')
def health(): return {"status":"ok","version":"0.2.0","mode":"hybrid-rules-plus-optional-llm"}

@app.get('/catalog')
def catalog():
 return {"levels":[{"id":"basic","label":"Ciclo básico"},{"id":"clinical","label":"Ciclo clínico"},{"id":"internship","label":"Internado"}],
 "modes":[{"id":"learning","label":"Aprendizaje con pistas"},{"id":"exam","label":"Examen sin pistas"}],
 "modules":["simulador","academia","mesa-oral","evaluaciones","flashcards","dashboard","planificador","apuntes"]}

@app.get('/cases/{case_id}')
def get_case(case_id:str, mode:str='exam'):
 if case_id!='acs-001': raise HTTPException(404,'Caso no encontrado')
 if mode not in ('learning','exam'): raise HTTPException(400,'Modo inválido')
 c=load_case(); data={k:v for k,v in c.items() if k not in ('patient_script','answer_key')}
 data['mode']=mode
 if mode=='learning': data['learning_objectives']=["Reconocer dolor torácico de alto riesgo","Interpretar ECG","Priorizar reperfusión"]
 return data

@app.post('/attempts')
def create_attempt(case_id:str='acs-001',mode:str='exam',level:str='clinical'):
 if case_id!='acs-001': raise HTTPException(404,'Caso no encontrado')
 if mode not in ('learning','exam') or level not in ('basic','clinical','internship'): raise HTTPException(400,'Configuración inválida')
 aid=str(uuid4()); attempts[aid]={"case_id":case_id,"mode":mode,"level":level,"stage":STAGES[0],"actions":[],"status":"active"}
 return {"attempt_id":aid,"stage":STAGES[0],"mode":mode,"level":level}

@app.post('/patient/ask')
def ask_patient(data:Ask):
 a=attempts.get(data.attempt_id)
 if not a: raise HTTPException(404,'Intento no encontrado')
 if a['stage']!='anamnesis': raise HTTPException(409,'La anamnesis está cerrada')
 result=respond(data.question)
 if a['mode']=='learning' and result.get('facts_retrieved'):
  result['teaching_note']='Buena pregunta: registra el dato y relaciónalo con la probabilidad pretest.'
 a['actions'].append({"type":"patient_question","question":data.question,"result":result})
 return result

@app.post('/attempts/action')
def register_action(data:Action):
 a=attempts.get(data.attempt_id)
 if not a: raise HTTPException(404,'Intento no encontrado')
 # La solicitud se registra; la publicación de resultados se resuelve desde el guion y reglas del caso.
 a['actions'].append({"type":data.action_type,"payload":data.payload})
 return {"registered":True,"action_count":len(a['actions'])}

@app.post('/attempts/{attempt_id}/advance')
def advance(attempt_id:str,target:str):
 a=attempts.get(attempt_id)
 if not a: raise HTTPException(404,'Intento no encontrado')
 if not can_advance(a['stage'],target): raise HTTPException(409,'Transición no permitida')
 a['stage']=target
 return {"stage":target}

@app.get('/attempts/{attempt_id}/stage-result')
def get_stage_result(attempt_id:str):
 a=attempts.get(attempt_id)
 if not a: raise HTTPException(404,'Intento no encontrado')
 try: result=stage_result(load_case(),a['stage'])
 except ValueError: raise HTTPException(409,'No hay resultados disponibles para esta etapa')
 if a['mode']=='exam' and a['stage']!='debrief' and 'expected_complications' in result:
  result={k:v for k,v in result.items() if k!='expected_complications'}
 a['actions'].append({"type":"stage_result_viewed","stage":a['stage']})
 return result

@app.get('/attempts/{attempt_id}')
def get_attempt(attempt_id:str):
 if attempt_id not in attempts: raise HTTPException(404,'Intento no encontrado')
 return attempts[attempt_id]

@app.get('/oral/{case_id}')
def oral(case_id:str):
 if case_id!='acs-001': raise HTTPException(404,'Caso no encontrado')
 return oral_session('Dolor torácico agudo')

@app.get('/flashcards')
def flashcards(): return FLASHCARDS+custom_cards

@app.post('/flashcards')
def create_card(data:CardCreate):
 c=make_flashcard(data.front,data.back,data.tags); custom_cards.append(c); return c

@app.post('/flashcards/{card_id}/review')
def review_card(card_id:str,data:Review):
 if not any(c['id']==card_id for c in FLASHCARDS+custom_cards): raise HTTPException(404,'Tarjeta no encontrada')
 state=review_sm2(card_states.get(card_id,{}),data.quality); card_states[card_id]=state; return state

@app.get('/dashboard')
def dashboard():
 # En producción: consulta agregada por usuario autenticado en PostgreSQL.
 demo=[{"status":"completed","duration_minutes":32,"domain_scores":{"fisiopatologia":55,"diagnostico":80,"terapeutica":45}},
       {"status":"completed","duration_minutes":28,"domain_scores":{"fisiopatologia":65,"diagnostico":75,"terapeutica":50}}]
 return summarize_attempts(demo)

@app.post('/planner/weekly')
def planner(data:PlanRequest):
 if any(v<0 or v>1 for v in data.weaknesses.values()): raise HTTPException(400,'Dominio debe estar entre 0 y 1')
 return weekly_plan(data.exam_date,data.hours_per_week,data.weaknesses)

@app.post('/attempts/{attempt_id}/finish')
def finish_attempt(attempt_id:str, critical_error:bool=False):
 a=attempts.get(attempt_id)
 if not a: raise HTTPException(404,'Intento no encontrado')
 criteria=[Criterion('Identificación del problema',.15,3,['Registro de hipótesis del estudiante'],'Revisar evidencia clínica.'),
 Criterion('Hipótesis diagnósticas',.20,3,['Diferenciales registrados'],'Jerarquizar por probabilidad y riesgo.'),
 Criterion('Análisis de datos',.20,3,['Interpretación registrada'],'Relacionar datos con hipótesis.'),
 Criterion('Planificación de exámenes',.15,3,['Estudios solicitados'],'Priorizar estudios que cambian conducta.'),
 Criterion('Manejo terapéutico',.20,3,['Plan terapéutico registrado'],'Justificar intervención y contraindicaciones.'),
 Criterion('Comunicación y justificación',.10,3,['Argumentación registrada'],'Explicar razonamiento con claridad.')]
 result=evaluate(criteria,critical_error)
 a['status']='completed'; a['evaluation']=result
 return result

@app.post('/demo/evaluate')
def demo_evaluate():
 cs=[Criterion('Identificación del problema',.15,4,['Reconoció IAMCEST anterior'],'Identificación correcta.'),
 Criterion('Hipótesis diagnósticas',.20,3,['Priorizó SCA'],'Jerarquizar mejor diferenciales.'),
 Criterion('Análisis de datos',.20,4,['Interpretó elevación ST V1-V4'],'Integración correcta.'),
 Criterion('Planificación de exámenes',.15,3,['Solicitó ECG y troponina'],'No retrasar reperfusión por biomarcadores.'),
 Criterion('Manejo terapéutico',.20,3,['Activó circuito de reperfusión'],'Explicitar estrategia y contraindicaciones.'),
 Criterion('Comunicación y justificación',.10,3,['Justificó prioridad'],'Comunicación clara.')]
 return evaluate(cs,False)

CONTENT_DIR = Path(__file__).resolve().parent / "content" / "aulas"

@app.get("/lessons")
def list_lessons():
    if not CONTENT_DIR.exists():
        return {"lessons": []}

    lessons = []
    for file in CONTENT_DIR.glob("*.md"):
        lessons.append({
            "id": file.stem,
            "title": file.stem.replace("_", " ").title()
        })

    return {"lessons": lessons}


@app.get("/lessons/{lesson_id}")
def get_lesson(lesson_id: str):
    file = CONTENT_DIR / f"{lesson_id}.md"

    if not file.is_file() or file.parent != CONTENT_DIR:
        raise HTTPException(404, "Aula não encontrada")

    return {
        "id": lesson_id,
        "content": file.read_text(encoding="utf-8")
    }
