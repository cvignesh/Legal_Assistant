"""
Parser Manager - Main orchestrator for PDF parsing
"""
from pathlib import Path
from typing import Optional

from .models import DocumentResult, ParsingMode
from .utils import (
    extract_text_from_pdf,
    detect_act_name,
    detect_parsing_mode,
    detect_chapters
)
from .strategies import get_strategy


class ParserManager:
    """
    Main orchestrator for parsing legal PDF documents.
    
    Usage:
        manager = ParserManager()
        result = manager.process_pdf("path/to/document.pdf")
    """
    
    def __init__(self, mode_override: Optional[ParsingMode] = None):
        """
        Initialize the parser manager.
        
        Args:
            mode_override: Optional mode to use instead of auto-detection
        """
        self.mode_override = mode_override
    
    def process_pdf(self, pdf_path: str) -> DocumentResult:
        """
        Process a PDF file and extract chunks.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            DocumentResult with all extracted chunks and metadata
        """
        pdf_path = Path(pdf_path)
        errors = []
        
        # Step 1: Extract text from PDF
        try:
            pages = extract_text_from_pdf(str(pdf_path))
        except Exception as e:
            return DocumentResult(
                filename=pdf_path.name,
                act_name="Unknown",
                act_short="Unknown",
                parsing_mode=ParsingMode.NARRATIVE,
                total_pages=0,
                total_chunks=0,
                chunks=[],
                errors=[f"Failed to extract text: {str(e)}"]
            )
        
        if not pages:
            return DocumentResult(
                filename=pdf_path.name,
                act_name="Unknown",
                act_short="Unknown",
                parsing_mode=ParsingMode.NARRATIVE,
                total_pages=0,
                total_chunks=0,
                chunks=[],
                errors=["No pages extracted from PDF"]
            )
        
        # Step 2: Detect act name
        try:
            act_name, act_short = detect_act_name(pages)
        except Exception as e:
            errors.append(f"Act name detection failed: {str(e)}")
            act_name = pdf_path.stem
            act_short = pdf_path.stem[:10]
        
        # Step 3: Detect parsing mode
        if self.mode_override:
            mode = self.mode_override
        else:
            try:
                mode_str = detect_parsing_mode(pages)
                mode = ParsingMode(mode_str)
            except Exception as e:
                errors.append(f"Mode detection failed: {str(e)}")
                mode = ParsingMode.NARRATIVE
        
        # Step 4: Detect chapters
        try:
            chapters = detect_chapters(pages)
        except Exception as e:
            errors.append(f"Chapter detection failed: {str(e)}")
            chapters = {}
        
        # Step 5: Get appropriate strategy and parse
        try:
            strategy = get_strategy(mode, act_name, act_short, chapters)
            chunks = strategy.parse(pages)
        except Exception as e:
            errors.append(f"Parsing failed: {str(e)}")
            chunks = []
        
        return DocumentResult(
            filename=pdf_path.name,
            act_name=act_name,
            act_short=act_short,
            parsing_mode=mode,
            total_pages=len(pages),
            total_chunks=len(chunks),
            chunks=chunks,
            errors=errors
        )
