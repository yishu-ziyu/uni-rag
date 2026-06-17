"""Unit tests for the export module (Markdown + PDF)."""
import pytest


def test_weasyprint_importable():
    """Sanity check: weasyprint installed and version meets the floor."""
    import weasyprint  # noqa: F401
    assert weasyprint.__version__ >= "60.0"
