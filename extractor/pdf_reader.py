import os
import fitz  # PyMuPDF
import pdfplumber
import numpy as np
from PIL import Image
import io

# Try importing OCR engines safely
HAS_EASYOCR = False
HAS_PYTESSERACT = False

try:
    import easyocr
    reader_ocr = easyocr.Reader(['en'], gpu=False)
    HAS_EASYOCR = True
except Exception as e:
    reader_ocr = None

try:
    import pytesseract
    HAS_PYTESSERACT = True
except Exception as e:
    pass

class PDFReader:
    """
    Extracts text, metadata, visual hierarchy, and tables from PDF pages.
    Includes OCR fallback for scanned pages.
    """
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.total_pages = len(self.doc)

    def extract_all_pages(self, progress_callback=None):
        pages_data = []
        
        # Open with pdfplumber too for table extraction
        plumber_doc = None
        try:
            plumber_doc = pdfplumber.open(self.pdf_path)
        except Exception:
            pass

        for page_num in range(1, self.total_pages + 1):
            if progress_callback:
                progress_callback(page_num, self.total_pages)

            fitz_page = self.doc[page_num - 1]
            raw_text = fitz_page.get_text("text").strip()
            
            used_ocr = False
            ocr_confidence = 100.0

            # If page text is very sparse (<30 printable chars), check if page has image & run OCR
            if len(raw_text) < 30:
                ocr_text, confidence = self._ocr_page(fitz_page)
                if ocr_text and len(ocr_text) > len(raw_text):
                    raw_text = ocr_text
                    used_ocr = True
                    ocr_confidence = confidence

            # Extract detailed block hierarchy (font sizes, flags for bolding)
            blocks = []
            fitz_blocks = fitz_page.get_text("dict").get("blocks", [])
            for b in fitz_blocks:
                if b.get("type") == 0:  # text block
                    for line in b.get("lines", []):
                        line_text = ""
                        max_size = 0
                        is_bold = False
                        for span in line.get("spans", []):
                            line_text += span.get("text", "")
                            max_size = max(max_size, span.get("size", 10))
                            flags = span.get("flags", 0)
                            if flags & 2 or "bold" in span.get("font", "").lower():
                                is_bold = True
                        if line_text.strip():
                            blocks.append({
                                "text": line_text.strip(),
                                "size": round(max_size, 1),
                                "bold": is_bold,
                                "bbox": line.get("bbox")
                            })

            # Extract tables using pdfplumber if available
            tables = []
            if plumber_doc and page_num <= len(plumber_doc.pages):
                try:
                    p_page = plumber_doc.pages[page_num - 1]
                    extracted_tables = p_page.extract_tables()
                    for t in extracted_tables:
                        if t:
                            # clean empty cells
                            cleaned_t = [[cell.strip() if cell else "" for cell in row] for row in t]
                            tables.append(cleaned_t)
                except Exception:
                    pass

            pages_data.append({
                "page": page_num,
                "text": raw_text,
                "blocks": blocks,
                "tables": tables,
                "used_ocr": used_ocr,
                "ocr_confidence": ocr_confidence
            })

        if plumber_doc:
            try:
                plumber_doc.close()
            except Exception:
                pass

        return pages_data

    def _ocr_page(self, fitz_page):
        try:
            pix = fitz_page.get_pixmap(dpi=150)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            
            if HAS_EASYOCR and reader_ocr:
                img_np = np.array(img)
                results = reader_ocr.readtext(img_np)
                texts = []
                confidences = []
                for res in results:
                    texts.append(res[1])
                    confidences.append(res[2])
                avg_conf = (sum(confidences) / len(confidences) * 100) if confidences else 80.0
                return "\n".join(texts), round(avg_conf, 1)

            elif HAS_PYTESSERACT:
                ocr_text = pytesseract.image_to_string(img)
                return ocr_text.strip(), 75.0

        except Exception as e:
            print(f"OCR Error on page: {e}")
        return "", 0.0

    def close(self):
        if self.doc:
            self.doc.close()
