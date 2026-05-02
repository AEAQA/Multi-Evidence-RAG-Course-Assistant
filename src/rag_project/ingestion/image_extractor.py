"""Image-aware PDF extraction utilities."""

from __future__ import annotations

from pathlib import Path

import fitz

from rag_project.ingestion.text_loader import default_doc_id
from rag_project.schemas import Chunk, ChunkMetadata
from rag_project.vision.caption_client import MockVisionCaptionClient, VisionCaptionClient

DEFAULT_IMAGE_OUTPUT_DIR = Path("data") / "processed" / "images"
FALLBACK_IMAGE_CAPTION = "Image extracted from PDF."


def extract_pdf_image_chunks(
    path: str | Path,
    *,
    output_dir: str | Path = DEFAULT_IMAGE_OUTPUT_DIR,
    doc_id: str | None = None,
    caption_client: VisionCaptionClient | None = None,
) -> list[Chunk]:
    """Extract embedded PDF images as retrievable image chunks.

    Failures for one image are skipped so image-aware ingestion can continue.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    if not file_path.is_file():
        raise ValueError(f"PDF path is not a file: {file_path}")

    resolved_doc_id = doc_id or default_doc_id(file_path)
    resolved_output_dir = Path(output_dir)
    try:
        resolved_output_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return []
    client = caption_client or MockVisionCaptionClient()
    chunks: list[Chunk] = []

    try:
        document = fitz.open(file_path)
    except Exception as exc:  # pragma: no cover - depends on fitz internals
        raise ValueError(f"Could not open PDF: {file_path}") from exc

    with document:
        for page_index, page in enumerate(document, start=1):
            page_image_count = 0
            for image_info in page.get_images(full=True):
                xref = int(image_info[0])
                rects = page.get_image_rects(xref)
                if not rects:
                    rects = [None]
                for rect in rects:
                    page_image_count += 1
                    chunk = _build_image_chunk(
                        document=document,
                        page=page,
                        page_number=page_index,
                        xref=xref,
                        rect=rect,
                        page_image_count=page_image_count,
                        file_path=file_path,
                        output_dir=resolved_output_dir,
                        doc_id=resolved_doc_id,
                        caption_client=client,
                    )
                    if chunk is not None:
                        chunks.append(chunk)

    return chunks


def _build_image_chunk(
    *,
    document: fitz.Document,
    page: fitz.Page,
    page_number: int,
    xref: int,
    rect: fitz.Rect | None,
    page_image_count: int,
    file_path: Path,
    output_dir: Path,
    doc_id: str,
    caption_client: VisionCaptionClient,
) -> Chunk | None:
    try:
        image = document.extract_image(xref)
        image_bytes = image["image"]
        extension = str(image.get("ext") or "png").lower()
        image_path = output_dir / (
            f"{doc_id}_p{page_number:03d}_img{page_image_count:04d}.{extension}"
        )
        image_path.write_bytes(image_bytes)
    except Exception:
        return None

    bbox = _rect_to_bbox(rect)
    nearby_text = _nearby_text(page, rect)
    caption = _caption_with_fallback(caption_client, str(image_path), nearby_text)
    text = _image_text(caption=caption, nearby_text=nearby_text)
    chunk_id = f"{doc_id}_page{page_number:03d}_image_{page_image_count:04d}"

    return Chunk(
        chunk_id=chunk_id,
        doc_id=doc_id,
        source_file=file_path.name,
        page=page_number,
        type="image",
        text=text,
        metadata=ChunkMetadata(
            bbox=bbox,
            image_path=str(image_path),
            caption=caption,
            nearby_text=nearby_text,
        ),
    )


def _caption_with_fallback(
    caption_client: VisionCaptionClient,
    image_path: str,
    nearby_text: str | None,
) -> str:
    try:
        caption = caption_client.caption(image_path, nearby_text=nearby_text).caption
    except Exception:
        return FALLBACK_IMAGE_CAPTION
    return caption.strip() or FALLBACK_IMAGE_CAPTION


def _image_text(*, caption: str, nearby_text: str | None) -> str:
    parts = [caption]
    if nearby_text:
        parts.append(f"Nearby text: {nearby_text}")
    return " ".join(parts).strip() or FALLBACK_IMAGE_CAPTION


def _nearby_text(page: fitz.Page, rect: fitz.Rect | None) -> str | None:
    if rect is None:
        return _page_text_fallback(page)

    candidates: list[tuple[float, str]] = []
    try:
        for block in page.get_text("blocks"):
            if len(block) < 5:
                continue
            text = str(block[4]).strip()
            if not text:
                continue
            block_rect = fitz.Rect(block[:4])
            distance = _rect_distance(rect, block_rect)
            candidates.append((distance, text))
    except Exception:
        return _page_text_fallback(page)

    candidates.sort(key=lambda item: item[0])
    nearby = " ".join(text for _, text in candidates[:2]).strip()
    if nearby:
        return nearby[:500]
    return _page_text_fallback(page)


def _page_text_fallback(page: fitz.Page) -> str | None:
    try:
        text = page.get_text("text").strip()
    except Exception:
        return None
    return text[:500] if text else None


def _rect_distance(left: fitz.Rect, right: fitz.Rect) -> float:
    if left.intersects(right):
        return 0.0
    horizontal = max(right.x0 - left.x1, left.x0 - right.x1, 0.0)
    vertical = max(right.y0 - left.y1, left.y0 - right.y1, 0.0)
    return horizontal + vertical


def _rect_to_bbox(rect: fitz.Rect | None) -> list[float] | None:
    if rect is None:
        return None
    return [float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1)]
