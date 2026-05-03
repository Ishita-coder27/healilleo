import logging
from typing import List, Tuple
import pdfplumber

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# PDF TEXT + TABLE EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

class PDFReader:
    def read(self, pdf_path: str) -> Tuple[str, List[List], str]:
        text, tables = self._try_pdfplumber(pdf_path)
        method = "pdfplumber"

        if len(text.strip()) < 50:
            text2 = self._try_pymupdf(pdf_path)
            if len(text2.strip()) > len(text.strip()):
                text = text2
                method = "pymupdf"

        if len(text.strip()) < 50:
            text = self._try_ocr(pdf_path)
            method = "ocr"

        return text, tables, method

    def _try_pdfplumber(self, path: str) -> Tuple[str, List[List]]:
        full_text = ""
        all_tables: List[List] = []
        try:
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    full_text += (page.extract_text() or "") + "\n"
                    try:
                        tables = page.extract_tables()
                        if tables:
                            all_tables.extend(tables)
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"pdfplumber failed: {e}")
        return full_text, all_tables

    def _try_pymupdf(self, path: str) -> str:
        try:
            import fitz
            doc = fitz.open(path)
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            return text
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"PyMuPDF failed: {e}")
        return ""

    def _try_ocr(self, path: str) -> str:
        try:
            from pdf2image import convert_from_path
            import pytesseract
            images = convert_from_path(path, dpi=300)
            return "".join(pytesseract.image_to_string(img) + "\n" for img in images)
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"OCR failed: {e}")
        return ""