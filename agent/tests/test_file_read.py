from unittest.mock import MagicMock, patch

import pytest

from agent.skills.file_read import file_read


def test_file_read_missing_file():
    result = file_read("does/not/exist.txt")

    assert "not found" in result


def test_file_read_txt_file(tmp_path):
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Hello from a text file.", encoding="utf-8")

    with patch("agent.skills.file_read.BASE_DIR", tmp_path):
        result = file_read(str(txt_file))

    assert result == "Hello from a text file."


def test_file_read_pdf_file(tmp_path):
    pdf_file = tmp_path / "notes.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 fake bytes")

    mock_page_1 = MagicMock()
    mock_page_1.extract_text.return_value = "Page one text."
    mock_page_2 = MagicMock()
    mock_page_2.extract_text.return_value = "Page two text."

    mock_reader = MagicMock()
    mock_reader.pages = [mock_page_1, mock_page_2]

    with patch("agent.skills.file_read.PdfReader", return_value=mock_reader):
        with patch("agent.skills.file_read.BASE_DIR", tmp_path):
            result = file_read(str(pdf_file))

    assert result == "Page one text.\nPage two text."


def test_file_read_pdf_handles_broken_file(tmp_path):
    pdf_file = tmp_path / "broken.pdf"
    pdf_file.write_bytes(b"not a real pdf")

    with patch("agent.skills.file_read.PdfReader", side_effect=Exception("bad pdf")):
        with patch("agent.skills.file_read.BASE_DIR", tmp_path):
            result = file_read(str(pdf_file))

    assert "Error reading PDF" in result


def test_file_read_unsupported_extension(tmp_path):
    docx_file = tmp_path / "notes.docx"
    docx_file.write_text("irrelevant", encoding="utf-8")

    with patch("agent.skills.file_read.BASE_DIR", tmp_path):
        result = file_read(str(docx_file))

    assert "unsupported file type" in result


# --- Security: sandboxing tests ---


def test_file_read_rejects_relative_path_traversal(tmp_path):
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text("top secret", encoding="utf-8")

    with patch("agent.skills.file_read.BASE_DIR", sandbox):
        result = file_read("../secret.txt")

    assert result == "Error: path is outside the allowed directory."


def test_file_read_rejects_absolute_path_outside_sandbox(tmp_path):
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("not yours", encoding="utf-8")

    with patch("agent.skills.file_read.BASE_DIR", sandbox):
        result = file_read(str(outside))

    assert result == "Error: path is outside the allowed directory."


def test_file_read_rejects_symlink_escaping_sandbox(tmp_path):
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("not yours", encoding="utf-8")
    symlink = sandbox / "link.txt"

    try:
        symlink.symlink_to(outside)
    except OSError:
        pytest.skip("Symlink creation not permitted in this environment")

    with patch("agent.skills.file_read.BASE_DIR", sandbox):
        result = file_read("link.txt")

    assert result == "Error: path is outside the allowed directory."
