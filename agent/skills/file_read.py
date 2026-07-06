from pathlib import Path

from pypdf import PdfReader

FILE_READ_TOOL = {
    "type": "function",
    "function": {
        "name": "file_read",
        "description": "Read the text contents of a local .txt or .pdf file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the .txt or .pdf file"},
            },
            "required": ["path"],
        },
    },
}


def file_read(path: str) -> str:
    file_path = Path(path)

    if not file_path.exists():
        return f"Error: file not found at {path}"

    suffix = file_path.suffix.lower()

    if suffix == ".txt":
        return file_path.read_text(encoding="utf-8")

    if suffix == ".pdf":
        try:
            reader = PdfReader(str(file_path))
        except Exception as exc:
            return f"Error reading PDF: {exc}"
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)

    return f"Error: unsupported file type '{suffix}'. Only .txt and .pdf are supported."
