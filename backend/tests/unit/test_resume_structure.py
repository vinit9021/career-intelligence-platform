from app.parsers.base import ExtractedDocument
from app.parsers.structure import build_structured_resume


def test_structured_resume_extracts_core_sections() -> None:
    extracted = ExtractedDocument(
        raw_text="""Arnav Example
arnav@example.com | +91 98765 43210
https://linkedin.com/in/arnav

Professional Summary
Backend engineer building production APIs.

Technical Skills
Python, FastAPI | PostgreSQL; Docker

Education
B.Tech Electrical Engineering - IIT Ropar

Experience
Software Engineering Intern - Example Labs
Built asynchronous APIs.

Projects
Career Intelligence Platform
Implemented resume parsing.

Certifications
AWS Cloud Practitioner
""",
        page_count=2,
        requires_ocr=False,
        warnings=(),
    )

    content, metadata = build_structured_resume(
        extracted=extracted,
        source_type="pdf",
        parser_name="test-parser",
        parser_version="1.0",
    )

    assert content.contact.email == "arnav@example.com"
    assert content.contact.phone == "+91 98765 43210"
    assert content.contact.linkedin_url == "https://linkedin.com/in/arnav"
    assert content.summary == "Backend engineer building production APIs."
    assert content.skills == ["Python", "FastAPI", "PostgreSQL", "Docker"]
    assert content.education == ["B.Tech Electrical Engineering - IIT Ropar"]
    assert content.projects[0] == "Career Intelligence Platform"
    assert metadata.source_type == "pdf"
    assert metadata.requires_ocr is False
    assert metadata.warnings == []


def test_missing_sections_generate_warnings() -> None:
    _, metadata = build_structured_resume(
        extracted=ExtractedDocument(
            raw_text="Summary\nOnly a summary is available.",
            page_count=1,
            requires_ocr=False,
            warnings=(),
        ),
        source_type="pdf",
        parser_name="test-parser",
        parser_version="1.0",
    )

    assert "No 'skills' section was detected." in metadata.warnings
    assert "No 'projects' section was detected." in metadata.warnings
