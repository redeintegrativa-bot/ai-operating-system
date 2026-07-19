# OCR Engine
# Handles text extraction from images and PDFs using pytesseract
# Supports preprocessing and multiple output formats

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class OCREngine:
    def __init__(self):
        self._pytesseract_available = False
        self._pdf_available = False
        try:
            import pytesseract
            self._pytesseract_available = True
        except ImportError:
            logger.warning("pytesseract not installed; OCR unavailable")

        try:
            from pdf2image import convert_from_path
            self._pdf_available = True
        except ImportError:
            logger.warning("pdf2image not installed; PDF OCR limited")

    def extract_from_image(self, image_path: str, lang: str = "eng") -> Dict[str, Any]:
        """Extract text from an image file."""
        if not self._pytesseract_available:
            return {"text": "", "error": "pytesseract not installed"}

        if not os.path.exists(image_path):
            return {"text": "", "error": f"File not found: {image_path}"}

        try:
            from PIL import Image
            import pytesseract
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, lang=lang)
            data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)

            words = []
            for i, word in enumerate(data["text"]):
                if word.strip():
                    words.append({
                        "text": word,
                        "confidence": data["conf"][i],
                        "bbox": {
                            "x": data["left"][i],
                            "y": data["top"][i],
                            "w": data["width"][i],
                            "h": data["height"][i],
                        },
                    })

            return {
                "text": text.strip(),
                "words": words,
                "word_count": len(words),
                "language": lang,
            }
        except Exception as e:
            logger.error(f"OCR extraction failed for {image_path}: {e}")
            return {"text": "", "error": str(e)}

    def extract_from_pdf(self, pdf_path: str, lang: str = "eng", dpi: int = 300) -> Dict[str, Any]:
        """Extract text from a PDF file by converting pages to images then OCR."""
        if not os.path.exists(pdf_path):
            return {"pages": [], "error": f"File not found: {pdf_path}"}

        if self._pdf_available and self._pytesseract_available:
            return self._extract_pdf_with_pdf2image(pdf_path, lang, dpi)
        return self._extract_pdf_fallback(pdf_path)

    def _extract_pdf_with_pdf2image(self, pdf_path: str, lang: str, dpi: int) -> Dict[str, Any]:
        """Extract PDF text using pdf2image + pytesseract."""
        try:
            from pdf2image import convert_from_path
            import pytesseract

            images = convert_from_path(pdf_path, dpi=dpi)
            pages = []
            full_text_parts = []

            for i, img in enumerate(images):
                text = pytesseract.image_to_string(img, lang=lang)
                pages.append({"page": i + 1, "text": text.strip()})
                full_text_parts.append(text.strip())

            return {
                "pages": pages,
                "total_pages": len(pages),
                "full_text": "\n\n".join(full_text_parts),
            }
        except Exception as e:
            logger.error(f"PDF OCR failed for {pdf_path}: {e}")
            return {"pages": [], "error": str(e)}

    def _extract_pdf_fallback(self, pdf_path: str) -> Dict[str, Any]:
        """Fallback PDF text extraction without pdf2image."""
        try:
            import subprocess
            result = subprocess.run(
                ["pdftotext", pdf_path, "-"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                return {"pages": [], "full_text": result.stdout.strip()}
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        try:
            import PyPDF2
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                pages = []
                for i, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    pages.append({"page": i + 1, "text": text.strip()})
                full_text = "\n\n".join(p["text"] for p in pages)
                return {"pages": pages, "total_pages": len(pages), "full_text": full_text}
        except ImportError:
            pass

        return {"pages": [], "error": "No PDF library available (install pdf2image, pytesseract, or PyPDF2)"}

    def preprocess_image(self, image_path: str, output_path: str, mode: str = "grayscale") -> str:
        """Preprocess image for better OCR accuracy."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        try:
            from PIL import Image, ImageFilter, ImageEnhance
            img = Image.open(image_path)

            if mode == "grayscale":
                img = img.convert("L")
            elif mode == "binarize":
                img = img.convert("L").point(lambda x: 255 if x > 128 else 0)
            elif mode == "denoise":
                img = img.convert("L").filter(ImageFilter.MedianFilter())
            elif mode == "sharpen":
                img = img.convert("L").filter(ImageFilter.SHARPEN)
                img = ImageEnhance.Contrast(img).enhance(2.0)
            else:
                img = img.convert("L")

            img.save(output_path)
            return output_path
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            raise

    def is_available(self) -> Dict[str, bool]:
        """Check which OCR capabilities are available."""
        return {
            "pytesseract": self._pytesseract_available,
            "pdf2image": self._pdf_available,
        }
