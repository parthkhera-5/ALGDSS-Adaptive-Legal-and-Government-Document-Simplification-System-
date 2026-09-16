import re
from pathlib import Path

import pymupdf
from docx import Document


class DocumentProcessor:

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

    def load(self, file_path):
        """
        Load a document and return a list of page/document records.
        """

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        extension = path.suffix.lower()

        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {extension}. "
                f"Supported types: {self.SUPPORTED_EXTENSIONS}"
            )

        if extension == ".pdf":
            return self._load_pdf(path)

        if extension == ".docx":
            return self._load_docx(path)

        if extension == ".txt":
            return self._load_txt(path)

    def _load_pdf(self, path):
        records = []

        pdf = pymupdf.open(path)

        for page_number, page in enumerate(pdf, start=1):

            text = page.get_text("text").strip()

            if not text:
                continue

            records.append({
                "page": page_number,
                "text": text,
                "source": path.name
            })

        pdf.close()

        return records

    def _load_docx(self, path):
        document = Document(path)

        paragraphs = []

        for paragraph in document.paragraphs:
            text = paragraph.text.strip()

            if text:
                paragraphs.append(text)

        text = "\n".join(paragraphs)

        return [{
            "page": None,
            "text": text,
            "source": path.name
        }]

    def _load_txt(self, path):
        text = path.read_text(
            encoding="utf-8",
            errors="ignore"
        ).strip()

        return [{
            "page": None,
            "text": text,
            "source": path.name
        }]

    def detect_sections(self, records):
        """
        Detect basic legal sections and clauses.

        This is intentionally simple for now.
        We will improve legal-aware parsing later.
        """

        processed_records = []

        for record in records:

            text = record["text"]

            sections = self._find_sections(text)

            processed_records.append({
                **record,
                "sections": sections
            })

        return processed_records

    def _find_sections(self, text):

        patterns = [
            r"(?im)^(?:section|article)\s+\d+[^\n]*",
            r"(?im)^\d+\.\s+[A-Z][^\n]*",
            r"(?im)^\d+\.\d+\s+[A-Z][^\n]*",
            r"(?im)^(?:clause)\s+\d+[^\n]*"
        ]

        matches = []

        for pattern in patterns:

            found = re.findall(pattern, text)

            matches.extend(found)

        return list(dict.fromkeys(matches))

    def process(self, file_path):
        """
        Complete document processing pipeline.
        """

        records = self.load(file_path)

        records = self.detect_sections(records)

        return records