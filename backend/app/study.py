import json
import os
import re
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .llm import get_llm

router = APIRouter(prefix="/study", tags=["Estudo por temas"])


class StudyRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=180)
    level: Literal["basic", "clinical", "internship"] = "clinical"
    depth: Literal["standard", "deep"] = "deep"
    language: Literal["es", "pt"] = "es"


@router.get("/diagnostics")
def study_diagnostics():
    """Diagnóstico temporário: informa apenas presença/configuração, nunca valores secretos."""
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()
    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").strip()
    llm_module_name = get_llm.__module__

    return {
        "python_running": True,
        "study_module_loaded": True,
        "llm_module_loaded": llm_module_name in __import__("sys").modules,
        "api_key_detected": bool(api_key),
        "model_configured": bool(model),
        "base_url_configured": bool(base_url),
        "model_name": model if model else None,
        "llm_module": llm_module_name,
    }


@router.get("/status")
def study_status():
    configured = bool(os.getenv("LLM_API_KEY", "").strip())
    return {
        "available": configured,
        "provider": "OpenAI-compatible" if configured else None,
        "message": "Generación de capítulos disponible." if configured else "Falta configurar LLM_API_KEY en el backend de Render.",
    }


@router.post("/generate")
async def generate_study(data: StudyRequest):
    provider = get_llm()
    if not os.getenv("LLM_API_KEY", "").strip():
        raise HTTPException(
            status_code=503,
            detail="El generador aún no está conectado: configura LLM_API_KEY en las variables de entorno del backend de Render.",
        )

    language_name = "español" if data.language == "es" else "portugués"
    level_name = {
        "basic": "ciclo básico",
        "clinical": "ciclo clínico",
        "internship": "internado médico",
    }[data.level]
    depth_name = "muy profundo y detallado" if data.depth == "deep" else "estándar y didáctico"

    system_prompt = f"""
Eres un profesor universitario de medicina y editor de un manual clínico.
Escribe en {language_name}, con terminología médica precisa y explicaciones pedagógicas.
El público es estudiante de medicina de {level_name}. Profundidad: {depth_name}.

Genera material educativo riguroso, estructurado y clínicamente útil. Distingue hechos
establecidos de controversias y evidencia emergente. No inventes estudios, DOI, autores,
años, recomendaciones de guías ni cifras. Si no recuerdas una referencia con seguridad,
menciónala como fuente recomendada para consulta sin inventar edición ni año.
Incluye advertencias cuando una recomendación dependa del contexto, edad, embarazo,
comorbilidades o protocolos locales. No sustituyas juicio clínico ni protocolos vigentes.

Devuelve SOLAMENTE un objeto JSON válido, sin markdown ni texto externo, con esta estructura:
{{
 "title": "título del capítulo",
 "level": "{data.level}",
 "summary": "resumen de 2-4 párrafos",
 "learning_objectives": ["objetivo 1", "objetivo 2"],
 "sections": [
   {{"id":"conceptos","title":"Título de sección","content":"Contenido en Markdown, con subtítulos, listas y tablas cuando ayuden."}}
 ],
 "clinical_cases": [
   {{"title":"Caso 1","scenario":"Viñeta clínica suficiente","questions":["Pregunta 1","Pregunta 2"],"discussion":"Resolución razonada paso a paso"}}
 ],
 "questions": [
   {{"question":"Pregunta de evaluación","options":["A) ...","B) ...","C) ...","D) ..."],"correct_answer":"B","explanation":"Justificación de la respuesta y por qué importan los distractores."}}
 ],
 "references": ["Fuente o guía recomendada; no inventes detalles bibliográficos."]
}}

Para profundidad profunda, crea entre 8 y 12 secciones sustanciales, 2 casos clínicos
progresivos y 5 preguntas. Incluye definición, epidemiología, etiología, fisiopatología,
clasificaciones, manifestaciones clínicas, diagnóstico, diagnóstico diferencial,
tratamiento, complicaciones y seguimiento, seleccionando lo pertinente al tema.
Añade algoritmos de abordaje en texto cuando sean útiles. Evita repetir contenido.
"""

    user_prompt = (
        f"Prepara un capítulo médico completo sobre: {data.topic}. "
        f"Nivel: {level_name}. Profundidad: {depth_name}. "
        "Prioriza aplicación clínica, razonamiento diagnóstico y decisiones terapéuticas."
    )

    try:
        raw = await provider.generate(system_prompt, user_prompt)
        cleaned = raw.strip()
        cleaned = re.sub(r"^\s*```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```\s*$", "", cleaned)
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("La respuesta no contiene un objeto JSON.")
        chapter = json.loads(cleaned[start:end + 1])
        if not isinstance(chapter.get("sections"), list) or not chapter["sections"]:
            raise ValueError("El capítulo no contiene secciones válidas.")
        chapter["topic"] = data.topic
        chapter["level"] = data.level
        chapter["depth"] = data.depth
        chapter["generated_by"] = "AI"
        chapter["educational_notice"] = (
            "Contenido educativo generado por IA. Verifica dosis, criterios y conductas "
            "con guías vigentes y protocolos locales antes de aplicarlos."
        )
        return chapter
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"No se pudo generar un capítulo válido. Intenta reducir el tema o volver a intentarlo. Detalle: {str(exc)[:220]}",
        ) from exc
