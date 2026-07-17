"""hlzd-office-doc v0.1 lightweight — pure stdlib DOCX generator.

Scope (minimal v0.1):
  - generate_minimal_docx(output_path, title, body_lines, header_company)
  - add_letterhead (company info + logo placeholder)

Full file format conversion (DOCX/PDF/Excel/PPTX round-trip),
HLZD letterhead template rendering, and contract template
generation are scoped to v0.2 (depends on libreoffice / pandoc /
python-docx which require external install).
"""
from __future__ import annotations

import logging
import os
import sys
import zipfile
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple


_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s :: %(message)s"


def get_logger(name: str = "hlzd-office-doc") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler(stream=sys.stderr)
        h.setFormatter(logging.Formatter(_LOG_FORMAT))
        logger.addHandler(h)
        logger.setLevel(os.getenv("HLZD_LOG_LEVEL", "INFO").upper())
        logger.propagate = False
    return logger


# ================================================================
# Errors
# ================================================================

class OfficeDocError(Exception):
    def __init__(self, message: str, *, source: str = "hlzd-office-doc",
                 recoverable: bool = True):
        super().__init__(message)
        self.source = source
        self.recoverable = recoverable


# ================================================================
# DOCX XML helpers
# ================================================================

WORDML_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
RELS_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"


def _xml_escape(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def _build_paragraphs_xml(body_lines: Iterable[str],
                          letterhead: Optional[str] = None) -> str:
    """Build <w:p> XML for each line. First paragraph optional letterhead."""
    parts: List[str] = []
    if letterhead:
        parts.append(
            f'<w:p><w:pPr><w:jc w:val="right"/></w:pPr>'
            f'<w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">'
            f'{_xml_escape(letterhead)}</w:t></w:r></w:p>'
        )
    for line in body_lines:
        parts.append(
            f'<w:p><w:r><w:t xml:space="preserve">'
            f'{_xml_escape(line)}</w:t></w:r></w:p>'
        )
    return "".join(parts)


def _build_document_xml(paragraphs_xml: str) -> str:
    """Build the word/document.xml body."""
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{WORDML_NS}" xmlns:r="{RELS_NS}">
<w:body>
{paragraphs_xml}
<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr>
</w:body>
</w:document>'''


def _build_content_types_xml() -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="{CT_NS}">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>'''


def _build_rels_xml() -> str:
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{RELS_NS}">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''


# ================================================================
# High-level API
# ================================================================

def generate_minimal_docx(
    output_path: str,
    title: str,
    body_lines: List[str],
    *,
    letterhead: Optional[str] = None,
) -> str:
    """Generate a minimal valid .docx file at output_path.

    Returns the output_path on success.
    """
    if not title or not isinstance(title, str):
        raise OfficeDocError("title must be a non-empty string")
    if not isinstance(body_lines, list):
        raise OfficeDocError("body_lines must be a list of strings")

    # Prepend title as first paragraph (bold)
    title_para = (
        f'<w:p><w:pPr><w:jc w:val="center"/></w:pPr>'
        f'<w:r><w:rPr><w:b/><w:sz w:val="32"/></w:rPr>'
        f'<w:t xml:space="preserve">{_xml_escape(title)}</w:t></w:r></w:p>'
    )
    paragraphs = title_para + _build_paragraphs_xml(body_lines, letterhead=letterhead)
    document_xml = _build_document_xml(paragraphs)

    out_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _build_content_types_xml())
        zf.writestr("_rels/.rels", _build_rels_xml())
        zf.writestr("word/document.xml", document_xml)
    return out_path


def add_letterhead(
    company_name: str,
    *,
    address: str = "",
    phone: str = "",
    email: str = "",
    website: str = "",
) -> str:
    """Return a formatted letterhead string for embedding in a docx.

    Format: bold company name + newlined contact details.
    """
    lines = [f"**{company_name}**"]
    for v in (address, phone, email, website):
        if v:
            lines.append(v)
    return "\n".join(lines)


def standard_letterhead_hlzd() -> str:
    """Default HLZD letterhead (for company internal use; change for external)."""
    return add_letterhead(
        "深圳海联智达科技有限公司 / HLZD",
        address="深圳市南山区高新南一道 99 号",
        phone="+86 138 0001 9999",
        email="sales@hlzd.example",
        website="www.hlzd.example",
    )


# ================================================================
# Pipeline
# ================================================================

def run_pipeline(
    output_path: str,
    title: str,
    body_lines: List[str],
    *,
    letterhead: Optional[str] = None,
) -> Dict[str, Any]:
    """End-to-end: build + return summary dict."""
    out = generate_minimal_docx(output_path, title, body_lines, letterhead=letterhead)
    return {
        "output_path": out,
        "size_bytes": os.path.getsize(out),
        "title": title,
        "body_paragraphs": len(body_lines),
        "letterhead_used": letterhead is not None,
    }
