import io
import json
import os
import re
import secrets
from datetime import datetime, timezone
from urllib.parse import quote
from uuid import uuid4

import httpx
from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from pypdf import PdfReader
from docx import Document
import fitz
import pytesseract
from PIL import Image
from .chunking import chunk_text

router = APIRouter(prefix="/library", tags=["Biblioteca médica"])
MAX_FILE_SIZE = 30 * 1024 * 1024
LIBRARY_ADMIN_TOKEN = os.getenv("LIBRARY_ADMIN_TOKEN", "").strip()


def _authorize(token: str):
    if not LIBRARY_ADMIN_TOKEN:
        raise HTTPException(status_code=503, detail="Biblioteca protegida: configure LIBRARY_ADMIN_TOKEN nas variáveis de ambiente do backend.")
    if not secrets.compare_digest(token, LIBRARY_ADMIN_TOKEN):
        raise HTTPException(status_code=401, detail="Chave de acesso da biblioteca inválida")


def _storage_config():
    url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    bucket = os.getenv("SUPABASE_BUCKET", "medreason-library").strip()
    if not url or not key or not bucket:
        raise HTTPException(
            status_code=503,
            detail="Armazenamento não configurado. Defina SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY e SUPABASE_BUCKET no Render.",
        )
    return url, key, bucket


def _request(method: str, path: str, *, content=None, json_body=None, content_type=None):
    url, key, _ = _storage_config()
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    if content_type:
        headers["Content-Type"] = content_type
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.request(
                method,
                f"{url}/storage/v1{path}",
                headers=headers,
                content=content,
                json=json_body,
            )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Não foi possível conectar ao Supabase Storage.") from exc
    if response.is_error:
        try:
            payload = response.json()
            detail = payload.get("message") or payload.get("error") or response.text
        except ValueError:
            detail = response.text
        # Supabase commonly reports missing objects as HTTP 400 with "not found".
        if response.status_code == 404 or (response.status_code == 400 and "not found" in str(detail).lower()):
            raise HTTPException(status_code=404, detail="Objeto não encontrado no Supabase Storage")
        # Avoid exposing credentials or internal response headers.
        raise HTTPException(status_code=502, detail=f"Supabase Storage ({response.status_code}): {str(detail)[:400]}")
    return response


def _object_path(kind: str, name: str) -> str:
    _, _, bucket = _storage_config()
    return f"/object/{quote(bucket, safe='')}/{kind}/{quote(name, safe='')}"


def _upload_object(path: str, content: bytes, content_type: str):
    _request("POST", path, content=content, content_type=content_type)


def _download_object(path: str) -> bytes:
    return _request("GET", path).content


def _delete_objects(paths: list[str]):
    if not paths:
        return
    _, _, bucket = _storage_config()
    _request(
        "DELETE",
        f"/object/{quote(bucket, safe='')}",
        json_body={"prefixes": paths},
    )


def _extract_docx(content: bytes) -> tuple[str, int]:
    doc = Document(io.BytesIO(content))
    parts = []
    for paragraph in doc.paragraphs:
        value = paragraph.text.strip()
        if value:
            parts.append(value)
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip().replace("\\n", " ") for cell in row.cells]
            if any(cells):
                parts.append(" | ".join(cells))
    return "\\n\\n".join(parts), len(parts)


def _extract_pdf_details(content: bytes) -> tuple[str, int, list[int], list[int]]:
    """Extrai texto nativo e aplica OCR em páginas sem texto útil."""
    reader = PdfReader(io.BytesIO(content))
    if reader.is_encrypted:
        try:
            result = reader.decrypt("")
            if not result:
                raise ValueError("PDF protegido")
        except Exception as exc:
            raise HTTPException(status_code=422, detail="PDF protegido por senha não pode ser processado") from exc

    ocr_pages = []
    ocr_failed_pages = []
    page_text = []

    try:
        rendered_pdf = fitz.open(stream=content, filetype="pdf")
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Não foi possível renderizar o PDF para extração") from exc

    try:
        for number, page in enumerate(reader.pages, start=1):
            page_content = (page.extract_text() or "").strip()

            # Páginas digitalizadas normalmente não possuem camada de texto.
            # O limiar também captura páginas com uma camada de texto quase vazia.
            if len(page_content) < 40:
                try:
                    rendered_page = rendered_pdf.load_page(number - 1)
                    pixmap = rendered_page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                    image = Image.open(io.BytesIO(pixmap.tobytes("png")))
                    recognized = pytesseract.image_to_string(
                        image,
                        lang="spa+por",
                        config="--psm 6",
                    ).strip()
                    if recognized:
                        page_content = recognized
                        ocr_pages.append(number)
                    else:
                        ocr_failed_pages.append(number)
                except Exception:
                    ocr_failed_pages.append(number)

            if page_content:
                page_text.append(f"[Página {number}]\\n{page_content}")
            else:
                page_text.append(f"[Página {number}]\\n[OCR sem resultado; revisar esta página]")
    finally:
        rendered_pdf.close()

    return "\\n\\n".join(page_text), len(reader.pages), ocr_pages, ocr_failed_pages


def _extract_pdf(content: bytes) -> tuple[str, int]:
    """Compatibilidade com os pontos da API que só precisam de texto e páginas."""
    extracted_text, page_count, _, _ = _extract_pdf_details(content)
    return extracted_text, page_count

def _public_metadata(metadata: dict) -> dict:
    return {key: value for key, value in metadata.items() if key not in {"stored_name", "metadata_name"}}


def _load_metadata(document_id: str) -> dict:
    if not re.fullmatch(r"[0-9a-f]{32}", document_id):
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    path = _object_path("metadata", f"{document_id}.json")
    try:
        raw = _download_object(path)
        return json.loads(raw.decode("utf-8"))
    except HTTPException as exc:
        if exc.status_code == 502:
            raise HTTPException(status_code=404, detail="Documento não encontrado") from exc
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="Metadados do documento não puderam ser lidos") from exc


@router.post("/documents", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    discipline: str = Form(..., min_length=2, max_length=80),
    topic: str = Form("", max_length=120),
    document_type: str = Form("material didático", max_length=60),
    author: str = Form("", max_length=160),
    year: str = Form("", max_length=4),
    x_library_token: str = Header(default="", alias="X-Library-Token"),
):
    _authorize(x_library_token)
    _storage_config()
    original_name = (file.filename or "").replace("\\\\", "/").split("/")[-1]
    extension = os.path.splitext(original_name)[1].lower()
    if extension not in {".pdf", ".docx"}:
        raise HTTPException(status_code=415, detail="Formato não permitido. Envie apenas PDF ou DOCX.")
    content = await file.read(MAX_FILE_SIZE + 1)
    await file.close()
    if not content:
        raise HTTPException(status_code=400, detail="O arquivo está vazio")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="O tamanho máximo permitido é 30 MB")
    ocr_pages = []
    ocr_failed_pages = []
    if extension == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise HTTPException(status_code=415, detail="O arquivo não parece ser um PDF válido")
        extracted_text, page_count, ocr_pages, ocr_failed_pages = _extract_pdf_details(content)
    else:
        try:
            extracted_text, page_count = _extract_docx(content)
        except Exception as exc:
            raise HTTPException(status_code=415, detail="DOCX inválido ou corrompido") from exc

    document_id = uuid4().hex
    stored_name = f"{document_id}{extension}"
    metadata = {
        "id": document_id,
        "filename": original_name,
        "extension": extension.lstrip("."),
        "discipline": discipline.strip(),
        "topic": topic.strip(),
        "document_type": document_type.strip(),
        "author": author.strip(),
        "year": year.strip(),
        "size_bytes": len(content),
        "page_count": page_count,
        "text_characters": len(extracted_text),
        "ocr_pages": ocr_pages,
        "ocr_failed_pages": ocr_failed_pages,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "stored_name": stored_name,
    }
    file_path = _object_path("files", stored_name)
    metadata_path = _object_path("metadata", f"{document_id}.json")
    _upload_object(file_path, content, "application/pdf" if extension == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    try:
        _upload_object(metadata_path, json.dumps(metadata, ensure_ascii=False).encode("utf-8"), "application/json")
    except Exception:
        try:
            _delete_objects([f"files/{stored_name}"])
        except Exception:
            pass
        raise
    if not extracted_text.strip():
        extraction_status = "ocr_required"
    elif ocr_failed_pages:
        extraction_status = "ocr_partial"
    else:
        extraction_status = "text_extracted"
    return {**_public_metadata(metadata), "extraction_status": extraction_status}


@router.get("/documents")
def list_documents(x_library_token: str = Header(default="", alias="X-Library-Token")):
    _authorize(x_library_token)
    _, _, bucket = _storage_config()
    response = _request(
        "POST",
        f"/object/list/{quote(bucket, safe='')}",
        json_body={"prefix": "metadata", "limit": 1000, "offset": 0, "sortBy": {"column": "name", "order": "desc"}},
    )
    try:
        items = response.json()
    except ValueError as exc:
        raise HTTPException(status_code=502, detail="Resposta inválida do Supabase Storage") from exc
    documents = []
    for item in items:
        name = item.get("name", "")
        if not re.fullmatch(r"[0-9a-f]{32}\\.json", name):
            continue
        try:
            metadata = json.loads(_download_object(_object_path("metadata", name)).decode("utf-8"))
            documents.append(_public_metadata(metadata))
        except (HTTPException, UnicodeDecodeError, json.JSONDecodeError):
            continue
    documents.sort(key=lambda item: item.get("uploaded_at", ""), reverse=True)
    return {"documents": documents, "count": len(documents)}


@router.get("/documents/{document_id}")
def get_document(document_id: str, x_library_token: str = Header(default="", alias="X-Library-Token")):
    _authorize(x_library_token)
    metadata = _load_metadata(document_id)
    content = _download_object(_object_path("files", metadata["stored_name"]))
    if metadata["extension"] == "pdf":
        extracted_text, _ = _extract_pdf(content)
    else:
        extracted_text, _ = _extract_docx(content)
    return {**_public_metadata(metadata), "content": extracted_text}


@router.get("/documents/{document_id}/chunks")
def get_document_chunks(
    document_id: str,
    max_chars: int = 1200,
    overlap: int = 180,
    x_library_token: str = Header(default="", alias="X-Library-Token"),
):
    """Recupera fragmentos com referência às páginas, prontos para indexação RAG."""
    _authorize(x_library_token)
    if max_chars < 200 or max_chars > 4000:
        raise HTTPException(status_code=422, detail="max_chars deve estar entre 200 e 4000")
    if overlap < 0 or overlap >= max_chars:
        raise HTTPException(status_code=422, detail="overlap deve ser menor que max_chars")
    metadata = _load_metadata(document_id)
    content = _download_object(_object_path("files", metadata["stored_name"]))
    try:
        if metadata["extension"] == "pdf":
            extracted_text, _ = _extract_pdf(content)
        else:
            extracted_text, _ = _extract_docx(content)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Não foi possível extrair o texto para fragmentação") from exc

    chunks = chunk_text(extracted_text, max_chars=max_chars, overlap=overlap)
    return {
        "document_id": document_id,
        "filename": metadata["filename"],
        "discipline": metadata["discipline"],
        "topic": metadata["topic"],
        "chunk_count": len(chunks),
        "max_chars": max_chars,
        "overlap": overlap,
        "chunks": chunks,
    }


@router.delete("/documents/{document_id}")
def delete_document(document_id: str, x_library_token: str = Header(default="", alias="X-Library-Token")):
    _authorize(x_library_token)
    metadata = _load_metadata(document_id)
    _delete_objects([
        f"files/{metadata['stored_name']}",
        f"metadata/{document_id}.json",
    ])
    return {"deleted": True, "id": document_id}
