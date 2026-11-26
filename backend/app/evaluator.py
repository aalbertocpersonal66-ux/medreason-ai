from dataclasses import dataclass, asdict
from typing import List

@dataclass
class Criterion:
    name: str
    weight: float
    level: int
    evidence: List[str]
    feedback: str

def evaluate(criteria: List[Criterion], critical_error: bool = False):
    if len(criteria) != 6:
        raise ValueError("La rúbrica debe contener exactamente seis criterios.")
    if any(c.level not in (1, 2, 3, 4) for c in criteria):
        raise ValueError("Nivel inválido: use 1, 2, 3 o 4.")
    if abs(sum(c.weight for c in criteria) - 1.0) > 1e-6:
        raise ValueError("Los pesos deben sumar 1.0.")
    details, total = [], 0.0
    labels = {1: "Pobre", 2: "Aceptable", 3: "Bueno", 4: "Excelente"}
    for c in criteria:
        points = c.weight * c.level / 4 * 100
        total += points
        details.append({
            "criterion": c.name, "level": c.level,
            "level_label": labels[c.level], "weight": c.weight,
            "points": round(points, 2), "evidence": c.evidence,
            "feedback": c.feedback
        })
    classification = ("Excelente" if total >= 90 else "Bueno" if total >= 75
                      else "Aceptable" if total >= 60 else "Pobre")
    return {
        "raw_score": round(total, 2),
        "classification": classification,
        "critical_error": critical_error,
        "final_cap_applied": bool(critical_error),
        "reported_score": min(round(total, 2), 59.0) if critical_error else round(total, 2),
        "details": details
    }
