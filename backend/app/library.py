import json
import os
import re
import secrets
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from pypdf import PdfReader
from docx import Document

router = APIRouter(prefix="/library", tags=["Biblioteca médica"])
STORAGE_DIR = Path(os.getenv("LIBRARY_STORAGE_DIR", "/var/data/medreason-library")).resolve()
MAX_FILE_SIZE = 30 * 1024 * 1024
LIBRARY_ADMIN_TOKEN = os.getenv("LIBRARY_ADMIN_TOKEN", "").strip()


def _authorize(token: str):
    if not LIBRARY_ADMIN_TOKEN:
        raise HTTPException(status_code=503, detail="Biblioteca protegida: configure LIBRARY_ADMIN_TOKEN nas variáveis de ambiente do backend.")
    if not secrets.compare_digest(token, LIBRARY_ADMIN_TOKEN):
        raise HTTPException(status_code=401, detail="Chave de acesso da biblioteca inválida")

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def _ensure_storage():
    try:
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise HTTPException(status_code=503, detail="Armazenamento da biblioteca indisponível. Verifique LIBRARY_STORAGE_DIR e o disco persistente.") from exc


def _safe_id(document_id: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{32}", document_id):
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    return document_id


def _metadata_path(document_id: str) -> Path:
    return STORAGE_DIR / f"{_safe_id(document_id)}.json"


def _load_metadata(document_id: str) -> dict:
    path = _metadata_path(document_id)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="Metadados do documento não puderam ser lidos") from exc


def _extract_docx(path: Path) -> tuple[str, int]:
    doc = Document(str(path))
    parts = []
    for paragraph in doc.paragraphs:
        value = paragraph.text.strip()
        if value:
            parts.append(value)
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
            if any(cells):
                parts.append(" | ".join(cells))
    return "\n\n".join(parts), len(parts)


def _extract_pdf(path: Path) -> tuple[str, int]:
    reader = PdfReader(str(path))
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception as exc:
            raise HTTPException(status_code=422, detail="PDF protegido por senha não pode ser processado") from exc
    page_text = []
    for number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        page_text.append(f"[Página {number}]\n{text}" if text else f"[Página {number}]\n[Sem texto extraível; pode ser necessário OCR]")
    return "\n\n".join(page_text), len(reader.pages)


def _public_metadata(metadata: dict) -> dict:
    return {key: value for key, value in metadata.items() if key != "stored_name"}


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
    _ensure_storage()
    original_name = Path(file.filename or "").name
    extension = Path(original_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Formato não permitido. Envie apenas PDF ou DOCX.")
    content = await file.read(MAX_FILE_SIZE + 1)
    await file.close()
    if not content:
        raise HTTPException(status_code=400, detail="O arquivo está vazio")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="O tamanho máximo permitido é 30 MB")
    if extension == ".pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=415, detail="O arquivo não parece ser um PDF válido")
    if extension == ".docx":
        if not content.startswith(b"PK") or not zipfile.is_zipfile(__import__("io").BytesIO(content)):
            raise HTTPException(status_code=415, detail="O arquivo não parece ser um DOCX válido")
        try:
            with zipfile.ZipFile(__import__("io").BytesIO(content)) as archive:
                if "word/document.xml" not in archive.namelist():
                    raise HTTPException(status_code=415, detail="O arquivo ZIP não contém um documento DOCX válido")
        except zipfile.BadZipFile as exc:
            raise HTTPException(status_code=415, detail="DOCX inválido") from exc

    document_id = uuid4().hex
    stored_name = f"{document_id}{extension}"
    file_path = STORAGE_DIR / stored_name
    try:
        file_path.write_bytes(content)
        if extension == ".pdf":
            extracted_text, page_count = _extract_pdf(file_path)
        else:
            extracted_text, page_count = _extract_docx(file_path)
    except HTTPException:
        file_path.unlink(missing_ok=True)
        raise
    except Exception as exc:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="Não foi possível ler o documento. Verifique se o arquivo não está corrompido.") from exc

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
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "stored_name": stored_name,
    }
    try:
        _metadata_path(document_id).write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=503, detail="Não foi possível salvar os metadados do documento") from exc
    return {**_public_metadata(metadata), "extraction_status": "text_extracted" if extracted_text.strip() else "ocr_required"}


@router.get("/documents")
def list_documents(x_library_token: str = Header(default="", alias="X-Library-Token")):
    _authorize(x_library_token)
    _ensure_storage()
    documents = []
    for metadata_file in STORAGE_DIR.glob("*.json"):
        try:
            metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
            documents.append(_public_metadata(metadata))
        except (OSError, json.JSONDecodeError):
            continue
    documents.sort(key=lambda item: item.get("uploaded_at", ""), reverse=True)
    return {"documents": documents, "count": len(documents)}


@router.get("/documents/{document_id}")
def get_document(document_id: str, x_library_token: str = Header(default="", alias="X-Library-Token")):
    _authorize(x_library_token)
    metadata = _load_metadata(document_id)
    file_path = STORAGE_DIR / metadata["stored_name"]
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Arquivo original não encontrado no armazenamento")
    if metadata["extension"] == "pdf":
        content, _ = _extract_pdf(file_path)
    else:
        content, _ = _extract_docx(file_path)
    return {**_public_metadata(metadata), "content": content}


@router.delete("/documents/{document_id}")
def delete_document(document_id: str, x_library_token: str = Header(default="", alias="X-Library-Token")):
    _authorize(x_library_token)
    metadata = _load_metadata(document_id)
    (STORAGE_DIR / metadata["stored_name"]).unlink(missing_ok=True)
    _metadata_path(document_id).unlink(missing_ok=True)
    return {"deleted": True, "id": document_id}
