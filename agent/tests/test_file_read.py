from unittest.mock import MagicMock, patch

from agent.skills.file_read import file_read


def test_file_read_missing_file():
    result = file_read("does/not/exist.txt")

    assert "not found" in result


def test_file_read_txt_file(tmp_path):
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("Hello from a text file.", encoding="utf-8")

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
        result = file_read(str(pdf_file))

    assert result == "Page one text.\nPage two text."


def test_file_read_pdf_handles_broken_file(tmp_path):
    pdf_file = tmp_path / "broken.pdf"
    pdf_file.write_bytes(b"not a real pdf")

    with patch("agent.skills.file_read.PdfReader", side_effect=Exception("bad pdf")):
        result = file_read(str(pdf_file))

    assert "Error reading PDF" in result


def test_file_read_unsupported_extension(tmp_path):
    docx_file = tmp_path / "notes.docx"
    docx_file.write_text("irrelevant", encoding="utf-8")

    result = file_read(str(docx_file))

    assert "unsupported file type" in result
