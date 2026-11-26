from pathlib import Path
import json
CASE_PATH=Path(__file__).parent/'cases'/'acs.json'
STAGES=['anamnesis','physical_exam','tests','differentials','treatment','evolution','debrief']
def load_case(): return json.loads(CASE_PATH.read_text(encoding='utf-8'))
def can_advance(current,target):
    try: return STAGES.index(target)==STAGES.index(current)+1
    except ValueError: return False
def stage_result(case, stage):
    mapping={'physical_exam':'physical_exam','tests':'tests'}
    if stage in mapping: return case.get(mapping[stage],{})
    if stage=='evolution': return {'available':'La evolución se determina por las acciones y el guion del escenario; este MVP muestra una evolución didáctica estándar.','expected_complications':case.get('answer_key',{}).get('complications',[])}
    if stage=='differentials': return {'instruction':'Registre y jerarquice sus hipótesis; la clave diagnóstica permanece oculta hasta el debrief.'}
    if stage=='treatment': return {'instruction':'Registre la conducta, prioridades, contraindicaciones y justificación.'}
    if stage=='debrief': return {'answer_key':case.get('answer_key',{})}
    raise ValueError('Etapa sin resultados')
