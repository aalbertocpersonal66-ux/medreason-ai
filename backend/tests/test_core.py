from app.evaluator import Criterion, evaluate
from app.patient_agent import respond
from app.learning import review_sm2

def test_patient_is_script_bounded():
    r=respond('¿Dónde le duele y cuándo comenzó?')
    assert 'retroesternal' in r['answer'] or 'centro del pecho' in r['answer']
    assert r['grounded'] is True

def test_sm2_quality_low_resets():
    r=review_sm2({'repetitions':4,'interval_days':20,'ease_factor':2.5},1)
    assert r['repetitions']==0 and r['interval_days']==1

def test_rubric_total():
    cs=[Criterion(str(i),w,3,[], '') for i,w in enumerate([.15,.2,.2,.15,.2,.1])]
    assert evaluate(cs)['raw_score']==75.0
