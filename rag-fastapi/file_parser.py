from abc import ABC, abstractmethod
import logging

import PyPDF2
import pytesseract
import fitz  # PyMuPDF
from PIL import Image
import io

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """Abstract base class for all file parsers."""
    @abstractmethod
    def parse(self, filepath: str) -> str:
        pass


class TextParser(BaseParser):
    """Parses .txt files and returns the text content."""
    def parse(self, filepath: str) -> str:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()


class PDFParser(BaseParser):
    """
    Parses PDF files.
    - First tries PyPDF2 (fast, works for text-based PDFs)
    - Falls back to OCR using pytesseract + fitz (for image-based PDFs)
    """
    def parse(self, filepath: str) -> str:
        # Step 1: Try PyPDF2 first
        try:
            text = self._parse_with_pypdf2(filepath)
            if text.strip():
                logger.info(f"Parsed with PyPDF2: {filepath}")
                return text
        except Exception as e:
            logger.warning(f"PyPDF2 failed for {filepath}: {e}")

        # Step 2: Fallback to OCR
        logger.info(f"Falling back to OCR for: {filepath}")
        return self._parse_with_ocr(filepath)

    def _parse_with_pypdf2(self, filepath: str) -> str:
        text = ""
        with open(filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
        return text

    def _parse_with_ocr(self, filepath: str) -> str:
        text = ""
        doc = fitz.open(filepath)
        for page in doc:
            # Convert each page to an image
            pix = page.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            # Run OCR on the image
            text += pytesseract.image_to_string(img)
        return text


class ParserFactory:
    """
    Registry that maps file extensions to parser classes.
    Makes it easy to add new parsers in the future.
    """
    def __init__(self):
        self._parsers = {}

    def register(self, extension: str, parser: BaseParser):
        self._parsers[extension] = parser

    def get_parser(self, extension: str) -> BaseParser:
        parser = self._parsers.get(extension.lower())
        if not parser:
            raise ValueError(f"No parser registered for extension: {extension}")
        return parser

    """
    Single interface for parsing any supported file type.
    Internally uses ParserFactory to find the right parser.
    """
class FileParser:
    def __init__(self, filepath: str):
        self.filepath = filepath  # ← don't prepend /usercode/ here
        self._factory = ParserFactory()
        self._factory.register(".txt", TextParser())
        self._factory.register(".pdf", PDFParser())

    def parse(self) -> str:
        ext = self.filepath.rsplit(".", 1)[-1]
        ext = f".{ext.lower()}"
        parser = self._factory.get_parser(ext)
        return parser.parse(self.filepath)

   