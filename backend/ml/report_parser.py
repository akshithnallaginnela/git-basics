"""
Parses blood report PDFs or images using pytesseract OCR.
Extracts key biomarker values using regex pattern matching.
No paid APIs — fully open source (Tesseract OCR).
"""
import re
import io
from typing import Dict, Optional
from pathlib import Path

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    from pdf2image import convert_from_bytes
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


# ── Regex patterns for common blood report formats ────────────────────────────
PATTERNS = {
    "hemoglobin":       r"h[ae]moglobin[^\d]*(\d+\.?\d*)",
    "platelets":        r"platelet[^\d]*(\d+\.?\d*)",
    "wbc":              r"(?:wbc|white blood cell|leucocyte)[^\d]*(\d+\.?\d*)",
    "rbc":              r"(?:rbc|red blood cell|erythrocyte)[^\d]*(\d+\.?\d*)",
    "hematocrit":       r"h[ae]matocrit[^\d]*(\d+\.?\d*)",
    "total_cholesterol":r"(?:total cholesterol|cholesterol)[^\d]*(\d+\.?\d*)",
    "ldl":              r"ldl[^\d]*(\d+\.?\d*)",
    "hdl":              r"hdl[^\d]*(\d+\.?\d*)",
    "triglycerides":    r"triglyceride[^\d]*(\d+\.?\d*)",
    "creatinine":       r"creatinine[^\d]*(\d+\.?\d*)",
    "urea":             r"(?:urea|bun)[^\d]*(\d+\.?\d*)",
    "sgpt":             r"(?:sgpt|alt)[^\d]*(\d+\.?\d*)",
    "sgot":             r"(?:sgot|ast)[^\d]*(\d+\.?\d*)",
    "tsh":              r"tsh[^\d]*(\d+\.?\d*)",
    "hba1c":            r"hba1c[^\d]*(\d+\.?\d*)",
    "vitamin_d":        r"vitamin\s*d[^\d]*(\d+\.?\d*)",
    "vitamin_b12":      r"(?:vitamin\s*b12|b12)[^\d]*(\d+\.?\d*)",
    "iron":             r"(?:serum iron|iron)[^\d]*(\d+\.?\d*)",
}


class BloodReportParser:

    def parse_file(self, file_bytes: bytes, filename: str) -> Dict:
        """
        Main entry: accepts raw file bytes + filename.
        Returns dict of extracted biomarker values + raw OCR text.
        """
        ext = Path(filename).suffix.lower()

        if ext == ".pdf":
            text = self._pdf_to_text(file_bytes)
        elif ext in (".jpg", ".jpeg", ".png", ".bmp", ".tiff"):
            text = self._image_to_text(file_bytes)
        else:
            return {"error": f"Unsupported file type: {ext}"}

        if not text:
            return {"error": "Could not extract text from file"}

        values = self._extract_values(text)
        values["raw_text"] = text[:3000]  # store first 3000 chars
        return values

    def _pdf_to_text(self, file_bytes: bytes) -> Optional[str]:
        if not PDF_AVAILABLE:
            return None
        try:
            images = convert_from_bytes(file_bytes, dpi=200)
            return "\n".join(self._image_to_text(self._pil_to_bytes(img)) for img in images)
        except Exception as e:
            print(f"[ReportParser] PDF error: {e}")
            return None

    def _image_to_text(self, file_bytes: bytes) -> Optional[str]:
        if not OCR_AVAILABLE:
            return None
        try:
            img = Image.open(io.BytesIO(file_bytes))
            return pytesseract.image_to_string(img)
        except Exception as e:
            print(f"[ReportParser] OCR error: {e}")
            return None

    def _extract_values(self, text: str) -> Dict:
        text_lower = text.lower()
        result = {}
        for key, pattern in PATTERNS.items():
            match = re.search(pattern, text_lower)
            if match:
                try:
                    result[key] = float(match.group(1))
                except ValueError:
                    pass
        return result

    def _pil_to_bytes(self, img) -> bytes:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
