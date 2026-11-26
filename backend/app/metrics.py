from collections import defaultdict

def summarize_attempts(attempts: list[dict]):
    domains=defaultdict(list); completed=0; total_minutes=0
    for a in attempts:
        if a.get("status")=="completed": completed+=1
        total_minutes += a.get("duration_minutes",0)
        for domain, score in a.get("domain_scores",{}).items(): domains[domain].append(score)
    return {"completed_cases":completed,"study_minutes":total_minutes,
      "mastery":{k:round(sum(v)/len(v),1) for k,v in domains.items() if v},
      "attempt_count":len(attempts)}
