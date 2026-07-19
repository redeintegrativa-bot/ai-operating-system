# OCR Engine
# Handles text extraction from images and PDFs using multiple OCR backends
# Supports: Tesseract, EasyOCR, PaddleOCR with auto-selection and fallback

import logging
import os
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class OCRBackend(str, Enum):
    TESSERACT = "tesseract"
    EASYOCR = "easyocr"
    PADDLEOCR = "paddleocr"
    AUTO = "auto"


class OCREngine:
    def __init__(self, backend: str = "auto"):
        self._backend = OCRBackend(backend) if backend in [e.value for e in OCRBackend] else OCRBackend.AUTO
        self._pytesseract_available = False
        self._pdf_available = False
        self._easyocr_available = False
        self._paddleocr_available = False
        self._easyocr_reader = None
        self._paddleocr_engine = None

        try:
            import pytesseract
            self._pytesseract_available = True
        except ImportError:
            logger.warning("pytesseract not installed; Tesseract OCR unavailable")

        try:
            from pdf2image import convert_from_path
            self._pdf_available = True
        except ImportError:
            logger.warning("pdf2image not installed; PDF OCR limited")

        try:
            import easyocr
            self._easyocr_available = True
        except ImportError:
            logger.debug("easyocr not installed; EasyOCR unavailable")

        try:
            from paddleocr import PaddleOCR
            self._paddleocr_available = True
        except ImportError:
            logger.debug("paddleocr not installed; PaddleOCR unavailable")

    def _resolve_backend(self, requested: str | None) -> OCRBackend:
        """Resolve which backend to use, falling back through available backends."""
        if requested and requested != "auto":
            try:
                backend = OCRBackend(requested)
            except ValueError:
                logger.warning(f"Unknown OCR backend '{requested}', using auto")
                backend = OCRBackend.AUTO

            if backend == OCRBackend.TESSERACT and self._pytesseract_available:
                return OCRBackend.TESSERACT
            elif backend == OCRBackend.EASYOCR and self._easyocr_available:
                return OCRBackend.EASYOCR
            elif backend == OCRBackend.PADDLEOCR and self._paddleocr_available:
                return OCRBackend.PADDLEOCR
            else:
                logger.warning(f"Requested backend '{requested}' not available, falling back")

        # Auto mode: try in order of preference
        if self._pytesseract_available:
            return OCRBackend.TESSERACT
        elif self._easyocr_available:
            return OCRBackend.EASYOCR
        elif self._paddleocr_available:
            return OCRBackend.PADDLEOCR
        else:
            return OCRBackend.AUTO

    def _get_easyocr_reader(self, lang: str) -> Any:
        """Get or create EasyOCR reader (cached)."""
        lang_list = [l.strip() for l in lang.split(",")]
        cache_key = tuple(sorted(lang_list))
        if self._easyocr_reader is None or getattr(self, "_easyocr_langs", None) != cache_key:
            import easyocr
            self._easyocr_reader = easyocr.Reader(lang_list, gpu=False)
            self._easyocr_langs = cache_key
        return self._easyocr_reader

    def _get_paddleocr_engine(self, lang: str) -> Any:
        """Get or create PaddleOCR engine (cached)."""
        paddle_lang = self._map_lang_to_paddle(lang)
        if self._paddleocr_engine is None or getattr(self, "_paddleocr_lang", None) != paddle_lang:
            from paddleocr import PaddleOCR
            self._paddleocr_engine = PaddleOCR(use_angle_cls=True, lang=paddle_lang, show_log=False)
            self._paddleocr_lang = paddle_lang
        return self._paddleocr_engine

    @staticmethod
    def _map_lang_to_paddle(lang: str) -> str:
        """Map common language codes to PaddleOCR language names."""
        lang_map = {
            "eng": "en", "en": "en",
            "ita": "it", "it": "it",
            "fra": "fr", "fr": "fr",
            "deu": "de", "de": "de",
            "spa": "es", "es": "es",
            "por": "pt", "pt": "pt",
            "rus": "ru", "ru": "ru",
            "jpn": "japan", "japan": "japan",
            "kor": "korean", "korean": "korean",
            "chi_sim": "ch", "chinese": "ch",
            "chi_tra": "chinese_cht",
            "ara": "ar", "ar": "ar",
        }
        first_lang = lang.split(",")[0].strip().lower()
        return lang_map.get(first_lang, "en")

    def _extract_with_tesseract(self, image_path: str, lang: str) -> Dict[str, Any]:
        """Extract text using Tesseract OCR."""
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
                "backend": "tesseract",
            }
        except Exception as e:
            logger.error(f"Tesseract OCR failed for {image_path}: {e}")
            return {"text": "", "error": str(e), "backend": "tesseract"}

    def _extract_with_easyocr(self, image_path: str, lang: str) -> Dict[str, Any]:
        """Extract text using EasyOCR."""
        try:
            reader = self._get_easyocr_reader(lang)
            results = reader.readtext(image_path)

            words = []
            text_parts = []
            for bbox, text, conf in results:
                text_parts.append(text)
                x_min = min(p[0] for p in bbox)
                y_min = min(p[1] for p in bbox)
                x_max = max(p[0] for p in bbox)
                y_max = max(p[1] for p in bbox)
                words.append({
                    "text": text,
                    "confidence": round(conf * 100, 2),
                    "bbox": {
                        "x": int(x_min),
                        "y": int(y_min),
                        "w": int(x_max - x_min),
                        "h": int(y_max - y_min),
                    },
                })

            return {
                "text": " ".join(text_parts).strip(),
                "words": words,
                "word_count": len(words),
                "language": lang,
                "backend": "easyocr",
            }
        except Exception as e:
            logger.error(f"EasyOCR failed for {image_path}: {e}")
            return {"text": "", "error": str(e), "backend": "easyocr"}

    def _extract_with_paddleocr(self, image_path: str, lang: str) -> Dict[str, Any]:
        """Extract text using PaddleOCR."""
        try:
            engine = self._get_paddleocr_engine(lang)
            result = engine.ocr(image_path, cls=True)

            words = []
            text_parts = []
            if result and result[0]:
                for line in result[0]:
                    bbox_points, (text, conf) = line
                    text_parts.append(text)
                    x_min = min(p[0] for p in bbox_points)
                    y_min = min(p[1] for p in bbox_points)
                    x_max = max(p[0] for p in bbox_points)
                    y_max = max(p[1] for p in bbox_points)
                    words.append({
                        "text": text,
                        "confidence": round(conf * 100, 2),
                        "bbox": {
                            "x": int(x_min),
                            "y": int(y_min),
                            "w": int(x_max - x_min),
                            "h": int(y_max - y_min),
                        },
                    })

            return {
                "text": " ".join(text_parts).strip(),
                "words": words,
                "word_count": len(words),
                "language": lang,
                "backend": "paddleocr",
            }
        except Exception as e:
            logger.error(f"PaddleOCR failed for {image_path}: {e}")
            return {"text": "", "error": str(e), "backend": "paddleocr"}

    def extract_from_image(self, image_path: str, lang: str = "eng", backend: str | None = None) -> Dict[str, Any]:
        """Extract text from an image file with backend selection and fallback."""
        if not os.path.exists(image_path):
            return {"text": "", "error": f"File not found: {image_path}"}

        resolved = self._resolve_backend(backend)
        backends_to_try = self._get_backend_chain(resolved)

        for b in backends_to_try:
            if b == OCRBackend.TESSERACT and self._pytesseract_available:
                result = self._extract_with_tesseract(image_path, lang)
                if not result.get("error"):
                    return result
                logger.warning(f"Tesseract failed, trying next backend: {result.get('error')}")
            elif b == OCRBackend.EASYOCR and self._easyocr_available:
                result = self._extract_with_easyocr(image_path, lang)
                if not result.get("error"):
                    return result
                logger.warning(f"EasyOCR failed, trying next backend: {result.get('error')}")
            elif b == OCRBackend.PADDLEOCR and self._paddleocr_available:
                result = self._extract_with_paddleocr(image_path, lang)
                if not result.get("error"):
                    return result
                logger.warning(f"PaddleOCR failed, trying next backend: {result.get('error')}")

        return {"text": "", "error": "No OCR backend available or all backends failed"}

    def _get_backend_chain(self, primary: OCRBackend) -> List[OCRBackend]:
        """Get ordered list of backends to try (primary first, then fallbacks)."""
        all_backends = [OCRBackend.TESSERACT, OCRBackend.EASYOCR, OCRBackend.PADDLEOCR]
        chain = [primary] + [b for b in all_backends if b != primary]
        return chain

    def extract_from_pdf(self, pdf_path: str, lang: str = "eng", dpi: int = 300, backend: str | None = None) -> Dict[str, Any]:
        """Extract text from a PDF file by converting pages to images then OCR."""
        if not os.path.exists(pdf_path):
            return {"pages": [], "error": f"File not found: {pdf_path}"}

        resolved = self._resolve_backend(backend)

        if self._pdf_available and resolved == OCRBackend.TESSERACT and self._pytesseract_available:
            return self._extract_pdf_with_pdf2image(pdf_path, lang, dpi)

        if self._pdf_available:
            return self._extract_pdf_with_pdf2image_any(pdf_path, lang, dpi, resolved)

        return self._extract_pdf_fallback(pdf_path)

    def _extract_pdf_with_pdf2image(self, pdf_path: str, lang: str, dpi: int) -> Dict[str, Any]:
        """Extract PDF text using pdf2image + Tesseract."""
        try:
            from pdf2image import convert_from_path

            images = convert_from_path(pdf_path, dpi=dpi)
            pages = []
            full_text_parts = []

            for i, img in enumerate(images):
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    img.save(tmp.name)
                    result = self._extract_with_tesseract(tmp.name, lang)
                    os.unlink(tmp.name)
                text = result.get("text", "")
                pages.append({"page": i + 1, "text": text, "backend": "tesseract"})
                full_text_parts.append(text)

            return {
                "pages": pages,
                "total_pages": len(pages),
                "full_text": "\n\n".join(full_text_parts),
                "backend": "tesseract",
            }
        except Exception as e:
            logger.error(f"PDF OCR failed for {pdf_path}: {e}")
            return {"pages": [], "error": str(e)}

    def _extract_pdf_with_pdf2image_any(self, pdf_path: str, lang: str, dpi: int, backend: OCRBackend) -> Dict[str, Any]:
        """Extract PDF text using pdf2image + any available OCR backend."""
        try:
            from pdf2image import convert_from_path

            images = convert_from_path(pdf_path, dpi=dpi)
            pages = []
            full_text_parts = []

            extractors = {
                OCRBackend.TESSERACT: self._extract_with_tesseract,
                OCRBackend.EASYOCR: self._extract_with_easyocr,
                OCRBackend.PADDLEOCR: self._extract_with_paddleocr,
            }
            extractor = extractors.get(backend, self._extract_with_tesseract)

            for i, img in enumerate(images):
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    img.save(tmp.name)
                    result = extractor(tmp.name, lang)
                    os.unlink(tmp.name)
                text = result.get("text", "")
                pages.append({"page": i + 1, "text": text, "backend": backend.value})
                full_text_parts.append(text)

            return {
                "pages": pages,
                "total_pages": len(pages),
                "full_text": "\n\n".join(full_text_parts),
                "backend": backend.value,
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
            "easyocr": self._easyocr_available,
            "paddleocr": self._paddleocr_available,
            "pdf2image": self._pdf_available,
        }

    def get_backend(self) -> str:
        """Return the current default backend."""
        return self._backend.value
