from datetime import date

def weekly_plan(exam_date: date, hours_per_week: int, weaknesses: dict[str, float]):
    """Distribución de horas según brecha; horas asignadas suman las disponibles."""
    if hours_per_week < 1:
        raise ValueError("Debe reservar al menos una hora semanal.")
    if not weaknesses:
        weaknesses = {"repaso general": 0.5}
    weights = {area: max(0.05, 1.0 - mastery) for area, mastery in weaknesses.items()}
    total_weight = sum(weights.values())
    raw = {area: hours_per_week * weight / total_weight for area, weight in weights.items()}
    allocation = {area: int(value) for area, value in raw.items()}
    remainder = hours_per_week - sum(allocation.values())
    for area in sorted(raw, key=lambda k: raw[k] - int(raw[k]), reverse=True)[:remainder]:
        allocation[area] += 1
    days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    daily = {day: [] for day in days}
    remaining = allocation.copy()
    # Reparte bloques de una hora alternando áreas, conservando exactamente la asignación.
    slot = 0
    while any(remaining.values()):
        area = max(remaining, key=remaining.get)
        day = days[slot % len(days)]
        existing = next((x for x in daily[day] if x["area"] == area), None)
        if existing:
            existing["hours"] += 1
        else:
            daily[day].append({"area": area, "hours": 1,
                               "activity": "Recuperación activa + caso clínico + repaso espaciado"})
        remaining[area] -= 1
        slot += 1
    schedule = [{"day": day, "blocks": daily[day], "hours": sum(x["hours"] for x in daily[day])}
                for day in days if daily[day]]
    return {"exam_date": exam_date.isoformat(), "hours_per_week": hours_per_week,
            "allocation_hours": allocation, "schedule": schedule}
