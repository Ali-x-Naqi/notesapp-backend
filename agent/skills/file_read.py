from pathlib import Path

from decouple import config
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

BASE_DIR = Path(config("FILE_READ_ROOT", default="./agent/workspace")).resolve()


def _resolve_within_base(path: str) -> Path | None:
    """Resolve path against BASE_DIR and reject anything that escapes it.

    Handles both relative paths (joined onto BASE_DIR) and absolute paths
    (checked directly) - pathlib's `/` operator silently discards the left
    side when the right side is absolute, so an absolute `path` must be
    checked on its own rather than blindly joined with BASE_DIR first.
    Symlinks are followed via resolve(), so a symlink pointing outside
    BASE_DIR is caught by the same relative_to() check.
    """
    candidate = Path(path)
    unresolved = candidate if candidate.is_absolute() else BASE_DIR / candidate

    try:
        resolved = unresolved.resolve(strict=False)
        resolved.relative_to(BASE_DIR)
    except ValueError:
        return None

    return resolved


def file_read(path: str) -> str:
    file_path = _resolve_within_base(path)

    if file_path is None:
        return "Error: path is outside the allowed directory."

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
