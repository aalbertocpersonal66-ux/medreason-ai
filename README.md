# MedReason AI — MVP 0.2

Plataforma educativa de razonamiento clínico en español. Público: ciclo básico, ciclo clínico e internado. Modalidades: aprendizaje guiado y examen sin pistas. Arquitectura: reglas clínicas + LLM opcional.

## Ejecutar localmente
### API
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate | macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Documentación interactiva: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Abrir http://localhost:3000. La API local se configura en `frontend/app/page.tsx` (`API`).

### LLM opcional
Copiar `backend/.env.example` a `.env` y configurar `LLM_API_KEY`, `LLM_BASE_URL` y `LLM_MODEL`. El adaptador está preparado; la conversación del paciente de este prototipo sigue usando reglas de guion para mantener las respuestas acotadas.

### Tests
```bash
cd backend
pip install pytest
pytest
```

## Contenido
- Simulador y paciente virtual con guion cerrado.
- Modos aprendizaje/examen y niveles básico/clínico/internado.
- Evaluación por rúbrica explicable.
- Mesa oral, flashcards con SM-2 simplificado, dashboard y planificador.
- Esquema SQL PostgreSQL y shell PWA.
- Apunte PDF IAMCEST generado en iteración anterior.

## Limitaciones conocidas
La persistencia de API es en memoria; no hay autenticación ni aislamiento real entre usuarios. El LLM no está conectado al paciente virtual por defecto. La sección de academia es una estructura de navegación, no un CMS terminado. La PWA tiene manifiesto y service worker básico, sin estrategia offline completa. El caso es ficticio y educativo; no es un dispositivo médico ni debe utilizarse para decisiones asistenciales.

## Publicación en Internet (demo)

Consulta `DEPLOY_RENDER.md` y `render.yaml` para publicar frontend y API en Render mediante GitHub Blueprint. Esta versión es solo demostrativa: no tiene autenticación ni persistencia duradera; no introduzcas datos personales ni datos clínicos reales.
