"""Fragmentação de documentos médicos para preparação de busca RAG.

A divisão respeita marcadores de página e limites de parágrafo sempre que
possível. O overlap reduz a perda de contexto entre fragmentos consecutivos.
"""
import re

PAGE_MARKER = re.compile(r"\[Página\s+(\d+)\]")


def _split_long_text(text: str, max_chars: int) -> list[str]:
    """Divide texto longo preferindo limites de sentença, depois espaços."""
    remaining = text.strip()
    pieces = []
    while len(remaining) > max_chars:
        cut = remaining.rfind(". ", 0, max_chars + 1)
        if cut < int(max_chars * 0.55):
            cut = remaining.rfind(" ", 0, max_chars + 1)
        if cut < int(max_chars * 0.4):
            cut = max_chars
        else:
            cut += 1
        piece = remaining[:cut].strip()
        if piece:
            pieces.append(piece)
        remaining = remaining[cut:].strip()
    if remaining:
        pieces.append(remaining)
    return pieces


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 180) -> list[dict]:
    """Retorna fragmentos com índice e intervalo de páginas de origem."""
    if max_chars < 200 or overlap < 0 or overlap >= max_chars:
        raise ValueError("Parâmetros de chunking inválidos")
    if not text or not text.strip():
        return []

    matches = list(PAGE_MARKER.finditer(text))
    pages = []
    if matches:
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            page_number = int(match.group(1))
            page_text = text[match.end():end].strip()
            pages.append((page_number, page_number, page_text))
    else:
        pages.append((None, None, text.strip()))

    chunks = []
    current_parts = []
    current_length = 0
    current_start = None
    current_end = None

    def flush():
        nonlocal current_parts, current_length, current_start, current_end
        value = "\n\n".join(current_parts).strip()
        if value:
            chunks.append({
                "chunk_index": len(chunks),
                "page_start": current_start,
                "page_end": current_end,
                "text": value,
                "text_characters": len(value),
            })
        current_parts = []
        current_length = 0
        current_start = None
        current_end = None

    for page_start, page_end, page_text in pages:
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", page_text) if p.strip()]
        for paragraph in paragraphs:
            for piece in _split_long_text(paragraph, max_chars):
                separator_length = 2 if current_parts else 0
                if current_parts and current_length + separator_length + len(piece) > max_chars:
                    previous = "\n\n".join(current_parts)
                    flush()
                    tail = previous[-overlap:].strip() if overlap else ""
                    if tail:
                        current_parts = [tail]
                        current_length = len(tail)
                        current_start = page_start
                        current_end = page_end
                if not current_parts:
                    current_start = page_start
                current_end = page_end
                current_parts.append(piece)
                current_length += (2 if len(current_parts) > 1 else 0) + len(piece)
                if len(piece) >= max_chars:
                    flush()

    flush()
    return chunks
