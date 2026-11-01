"""Safe local normalization of PDF, PNG and JPEG CV documents.

Image CVs become a one-page, image-only PDF so the existing OCR, source quote
grounding, page citation, review and offline export pipeline stays unchanged.
Nothing here makes a Meta request or grants generated image text evidence status.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import io
import base64

import pymupdf as fitz
from PIL import Image, ImageOps, UnidentifiedImageError


PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"
MAX_IMAGE_PIXELS = 12_000_000


@dataclass(frozen=True)
class PreparedCv:
    pdf_bytes: bytes
    input_media_type: str
    original_sha256: str
    normalized_sha256: str
    converted_image_to_pdf: bool


def media_kind(data: bytes) -> str:
    if data.startswith(b"%PDF-"):
        return "application/pdf"
    if data.startswith(PNG_MAGIC):
        return "image/png"
    if data.startswith(JPEG_MAGIC):
        return "image/jpeg"
    raise ValueError("Upload a readable PDF, PNG or JPEG CV. Other files are not supported.")


def prepare_cv(data: bytes, *, max_bytes: int) -> PreparedCv:
    if not data:
        raise ValueError("The uploaded CV is empty.")
    if len(data) > max_bytes:
        raise ValueError("The uploaded CV exceeds the configured document size limit.")
    kind = media_kind(data)
    original = hashlib.sha256(data).hexdigest()
    if kind == "application/pdf":
        return PreparedCv(data, kind, original, original, False)
    try:
        with Image.open(io.BytesIO(data)) as original_image:
            if original_image.format != ("PNG" if kind == "image/png" else "JPEG"):
                raise ValueError("Image type does not match its file signature.")
            width, height = original_image.size
            if width < 50 or height < 50 or width * height > MAX_IMAGE_PIXELS:
                raise ValueError("Image CV dimensions are outside the supported limits.")
            if getattr(original_image, "n_frames", 1) != 1:
                raise ValueError("Animated and multi-frame image CVs are unsupported.")
            oriented = ImageOps.exif_transpose(original_image)
            oriented.load()
            # Flatten transparent PNGs onto white, keeping all source pixels
            # visible for existing local OCR and subsequent page verification.
            if oriented.mode in {"RGBA", "LA"} or "transparency" in oriented.info:
                rgba = oriented.convert("RGBA")
                rgb = Image.new("RGB", rgba.size, "white")
                rgb.paste(rgba, mask=rgba.getchannel("A"))
            else:
                rgb = oriented.convert("RGB")
            jpg = io.BytesIO()
            rgb.save(jpg, format="JPEG", quality=92, optimize=True)
            image_bytes = jpg.getvalue()
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
        if isinstance(exc, ValueError):
            raise
        raise ValueError("The image CV could not be decoded safely.") from exc

    # A4 page, no cropping and no guessed text geometry.
    document = fitz.open()
    try:
        page = document.new_page(width=595, height=842)
        inset = 20.0
        scale = min((595 - 2 * inset) / rgb.width, (842 - 2 * inset) / rgb.height)
        display_w, display_h = rgb.width * scale, rgb.height * scale
        left, top = (595 - display_w) / 2, (842 - display_h) / 2
        page.insert_image(fitz.Rect(left, top, left + display_w, top + display_h),
                          stream=image_bytes)
        pdf = document.tobytes(garbage=4, deflate=True)
    finally:
        document.close()
    if len(pdf) > max_bytes:
        raise ValueError("Converted image CV is too large for the analysis limit.")
    return PreparedCv(pdf, kind, original, hashlib.sha256(pdf).hexdigest(), True)


def optional_meta_vision_parts(
    pdf_bytes: bytes, ocr_page_numbers: list[int], *,
    max_pages: int = 2, max_edge: int = 1180
) -> list[dict]:
    """Build bounded, source-page-labelled Meta image content parts.

    Vision parts are supplementary layout context, not verified quotations.
    Only OCR pages are eligible; never include a full CV if the server did
    not explicitly request visual inspection after consent.
    """
    if not ocr_page_numbers or max_pages < 1:
        return []
    parts = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
        for page_number in sorted(set(ocr_page_numbers))[:min(max_pages, 2)]:
            if type(page_number) is not int or not (1 <= page_number <= len(document)):
                continue
            page = document[page_number - 1]
            if page.rect.width <= 0 or page.rect.height <= 0:
                continue
            pix = page.get_pixmap(matrix=fitz.Matrix(1.45, 1.45),
                                  alpha=False, colorspace=fitz.csRGB)
            with Image.open(io.BytesIO(pix.tobytes("png"))) as im:
                im.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
                out = io.BytesIO()
                im.convert("RGB").save(out, format="JPEG", quality=76, optimize=True)
                jpg = out.getvalue()
            if len(jpg) > 900_000:
                continue
            parts.extend([
                {"type": "text",
                 "text": f"Visual layout reference only: original CV PDF page {page_number}. "
                         "Use locally extracted page-labelled text for every exact quotation."},
                {"type": "image_url",
                 "image_url": {"url": "data:image/jpeg;base64," +
                                      base64.b64encode(jpg).decode("ascii")}},
            ])
    return parts
