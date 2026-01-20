import pytest
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.parser.manager import ParserManager
from app.services.parser.models import ParsingMode

SAMPLE_PDF = Path(__file__).parent.parent.parent.parent / "Sample_pdf" / "BNS.pdf"

def test_parser_manager_init():
    """Test ParserManager initialization."""
    manager = ParserManager()
    assert manager is not None

def test_process_pdf():
    """Test PDF processing."""
    if not SAMPLE_PDF.exists():
        pytest.skip(f"Sample PDF not found: {SAMPLE_PDF}")
    
    manager = ParserManager()
    result = manager.process_pdf(str(SAMPLE_PDF))
    
    assert result is not None
    assert result.filename == "BNS.pdf"
    assert result.act_name != "Unknown"
    assert result.total_chunks > 0
    assert len(result.chunks) == result.total_chunks
    assert result.parsing_mode == ParsingMode.NARRATIVE

def test_process_nonexistent_pdf():
    """Test processing non-existent PDF."""
    manager = ParserManager()
    result = manager.process_pdf("/fake/path/to/file.pdf")
    
    assert result.total_chunks == 0
    assert len(result.errors) > 0

def test_chunk_structure():
    """Test that chunks have required fields."""
    if not SAMPLE_PDF.exists():
        pytest.skip(f"Sample PDF not found: {SAMPLE_PDF}")
    
    manager = ParserManager()
    result = manager.process_pdf(str(SAMPLE_PDF))
    
    if result.chunks:
        chunk = result.chunks[0]
        assert hasattr(chunk, "chunk_id")
        assert hasattr(chunk, "text_for_embedding")
        assert hasattr(chunk, "raw_content")
        assert hasattr(chunk, "metadata")
        assert chunk.metadata.act_name != ""
