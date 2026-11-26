# Publicar MedReason AI (demo) en Render

Este repositorio incluye `render.yaml` para crear dos servicios en Render: API FastAPI y web Next.js.

## Antes de publicar

Esta versión es una DEMO educativa. No tiene autenticación, aislamiento entre estudiantes ni persistencia duradera: los intentos y revisiones se guardan en memoria y se pierden cuando el servicio se reinicia. No introduzcas datos personales, identificables ni información clínica real.

## Pasos

1. Crea una cuenta en https://render.com/ (puedes iniciar sesión con GitHub).
2. Crea un repositorio nuevo en GitHub y sube el contenido de esta carpeta, conservando `render.yaml` en la raíz.
3. En Render, elige **New + → Blueprint** y conecta ese repositorio.
4. Render detectará `render.yaml` y mostrará los servicios `medreason-ai-api` y `medreason-ai-web`. Confirma la creación.
5. Espera a que ambos servicios terminen el despliegue. El servicio web tendrá una URL pública `https://...onrender.com`.
6. Abre esa URL. La API tendrá su propia URL y el frontend la recibe automáticamente mediante `NEXT_PUBLIC_API_URL`.

## Limitaciones del plan gratuito

Los servicios gratuitos pueden entrar en suspensión por inactividad y tardar en responder al primer acceso. La disponibilidad, límites y condiciones del plan dependen de Render y pueden cambiar.

## Antes de invitar a otros estudiantes

Implementar autenticación, autorización y propiedad de intentos, PostgreSQL persistente, migraciones, límites de uso, registro seguro y política de privacidad. Revisar también la evaluación: algunas puntuaciones del MVP son demostrativas y no deben presentarse como calificación académica válida.
