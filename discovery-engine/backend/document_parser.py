import io
from pathlib import Path


def parse_document(filename: str, content: bytes) -> str:
    """Parse PDF, DOCX, or TXT and return plain text."""
    ext = Path(filename).suffix.lower()

    if ext == ".txt":
        return content.decode("utf-8", errors="ignore")

    if ext == ".pdf":
        import fitz  # PyMuPDF

        doc = fitz.open(stream=content, filetype="pdf")
        pages = [page.get_text() for page in doc]
        return "\n\n".join(pages)

    if ext in (".docx", ".doc"):
        from docx import Document

        doc = Document(io.BytesIO(content))
        parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                parts.append(para.text)
        return "\n".join(parts)

    raise ValueError(f"Unsupported file type: {ext}. Supported: .pdf, .docx, .txt")
