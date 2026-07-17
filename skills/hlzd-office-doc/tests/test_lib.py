"""Unit tests for hlzd-office-doc lightweight v0.1."""
from __future__ import annotations

import os
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import lib  # noqa: E402


# ================================================================
# generate_minimal_docx
# ================================================================

class TestGenerateMinimalDocx:
    def test_creates_file(self, tmp_path):
        out = tmp_path / "test.docx"
        result = lib.generate_minimal_docx(
            str(out), "Test Title", ["Line 1", "Line 2"],
        )
        assert Path(result).exists()
        assert Path(result).stat().st_size > 0

    def test_valid_zip_structure(self, tmp_path):
        out = tmp_path / "valid.docx"
        lib.generate_minimal_docx(str(out), "Title", ["body"])
        with zipfile.ZipFile(out, "r") as zf:
            names = set(zf.namelist())
        # 必备文件
        assert "[Content_Types].xml" in names
        assert "_rels/.rels" in names
        assert "word/document.xml" in names

    def test_content_types_xml(self, tmp_path):
        out = tmp_path / "test.docx"
        lib.generate_minimal_docx(str(out), "X", ["Y"])
        with zipfile.ZipFile(out, "r") as zf:
            ct = zf.read("[Content_Types].xml").decode("utf-8")
        assert "wordprocessingml.document.main" in ct

    def test_rels_xml(self, tmp_path):
        out = tmp_path / "test.docx"
        lib.generate_minimal_docx(str(out), "X", ["Y"])
        with zipfile.ZipFile(out, "r") as zf:
            rels = zf.read("_rels/.rels").decode("utf-8")
        assert "officeDocument" in rels

    def test_document_xml_contains_title(self, tmp_path):
        out = tmp_path / "test.docx"
        lib.generate_minimal_docx(str(out), "My Custom Title", ["body"])
        with zipfile.ZipFile(out, "r") as zf:
            doc = zf.read("word/document.xml").decode("utf-8")
        assert "My Custom Title" in doc

    def test_document_xml_contains_body_lines(self, tmp_path):
        out = tmp_path / "test.docx"
        lib.generate_minimal_docx(
            str(out), "T", ["Line A", "Line B", "Line C"],
        )
        with zipfile.ZipFile(out, "r") as zf:
            doc = zf.read("word/document.xml").decode("utf-8")
        for line in ["Line A", "Line B", "Line C"]:
            assert line in doc

    def test_letterhead_embedded(self, tmp_path):
        out = tmp_path / "test.docx"
        lib.generate_minimal_docx(
            str(out), "T", ["body"], letterhead="HLZD Co",
        )
        with zipfile.ZipFile(out, "r") as zf:
            doc = zf.read("word/document.xml").decode("utf-8")
        assert "HLZD Co" in doc

    def test_no_letterhead_when_omitted(self, tmp_path):
        out = tmp_path / "test.docx"
        lib.generate_minimal_docx(str(out), "T", ["body"])
        with zipfile.ZipFile(out, "r") as zf:
            doc = zf.read("word/document.xml").decode("utf-8")
        # Only 2 paragraphs (title + body)
        assert doc.count("<w:p>") == 2

    def test_xml_escapes_special_chars(self, tmp_path):
        out = tmp_path / "test.docx"
        lib.generate_minimal_docx(
            str(out), "T", ["<script>", "&", '"quote"'],
        )
        with zipfile.ZipFile(out, "r") as zf:
            doc = zf.read("word/document.xml").decode("utf-8")
        assert "&lt;script&gt;" in doc
        assert "&amp;" in doc
        assert "&quot;quote&quot;" in doc
        # raw < not inside attribute
        assert "<script>" not in doc

    def test_invalid_title_raises(self, tmp_path):
        with pytest.raises(lib.OfficeDocError):
            lib.generate_minimal_docx(str(tmp_path / "x.docx"), "", ["body"])

    def test_invalid_body_type_raises(self, tmp_path):
        with pytest.raises(lib.OfficeDocError):
            lib.generate_minimal_docx(str(tmp_path / "x.docx"), "T", "not a list")

    def test_creates_parent_dir(self, tmp_path):
        nested = tmp_path / "a" / "b" / "c"
        out = nested / "out.docx"
        lib.generate_minimal_docx(str(out), "T", ["b"])
        assert out.exists()


# ================================================================
# add_letterhead
# ================================================================

class TestAddLetterhead:
    def test_company_name_bold(self):
        result = lib.add_letterhead("ACME Co")
        assert "**ACME Co**" in result

    def test_includes_address(self):
        result = lib.add_letterhead("ACME", address="123 Main St")
        assert "123 Main St" in result

    def test_includes_all_optional_fields(self):
        result = lib.add_letterhead(
            "ACME", address="addr", phone="+1", email="a@b.c", website="w.com",
        )
        for s in ("addr", "+1", "a@b.c", "w.com"):
            assert s in result

    def test_omits_empty_fields(self):
        result = lib.add_letterhead("ACME")
        # only company name line
        lines = result.split("\n")
        assert len(lines) == 1


class TestStandardLetterheadHLZD:
    def test_includes_hlzd(self):
        result = lib.standard_letterhead_hlzd()
        assert "HLZD" in result
        assert "深圳" in result or "海联" in result


# ================================================================
# run_pipeline
# ================================================================

class TestRunPipeline:
    def test_returns_summary(self, tmp_path):
        out = tmp_path / "p.docx"
        result = lib.run_pipeline(
            str(out), "Title", ["Line1", "Line2"],
            letterhead="HLZD",
        )
        assert result["output_path"] == str(out)
        assert result["size_bytes"] > 0
        assert result["title"] == "Title"
        assert result["body_paragraphs"] == 2
        assert result["letterhead_used"] is True

    def test_size_grows_with_content(self, tmp_path):
        out1 = tmp_path / "small.docx"
        out2 = tmp_path / "big.docx"
        lib.run_pipeline(str(out1), "T", ["x"])
        lib.run_pipeline(str(out2), "T", ["x"] * 50)
        assert Path(out2).stat().st_size > Path(out1).stat().st_size
