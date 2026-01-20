"""
Utility functions for PDF text extraction and pattern detection
"""
import re
import fitz  # PyMuPDF
from typing import List, Tuple, Optional, Dict
from pathlib import Path
from app.services.parser.models import ParsingMode


def extract_text_from_pdf(pdf_path: str) -> List[Tuple[int, str]]:
    """
    Extract text from all pages of a PDF using PyMuPDF.
    Uses clipping to exclude margin notes (headers/footers/side margins).
    
    Assumes standard A4/Legal layout.
    """
    doc = fitz.open(pdf_path)
    pages = []
    
    for i, page in enumerate(doc):
        # Determine page width/height to set clip
        w = page.rect.width
        h = page.rect.height
        
        # Define clip box (ignore top 5%, bottom 5%, and very edges)
        # This helps exclude running headers/footers and side margin notes
        # Standard A4 is ~595 pts width.
        # Main text usually ends around 480 pts. Margin notes start around 485 pts.
        # We set right clip to w - 110 to exclude margin notes.
        clip_rect = fitz.Rect(30, 40, w - 110, h - 40)
        
        text = page.get_text(clip=clip_rect)
        pages.append((i + 1, text))  # 1-indexed page number
    
    doc.close()
    return pages


def detect_act_name(pages: List[Tuple[int, str]]) -> Tuple[str, str]:
    """
    Detect act name and short name from first few pages.
    Uses earliest match position to handle cross-references.
    
    Returns:
        Tuple of (full_name, short_name)
    """
    # Combine first 3 pages for detection
    first_pages_text = "\n".join([text for _, text in pages[:3]])
    
    # Patterns for common Indian Acts
    act_patterns = [
        (r'BHARATIYA\s+NYAYA\s+SANHITA', 'Bharatiya Nyaya Sanhita, 2023', 'BNS'),
        (r'BHARATIYA\s+NAGARIK\s+SURAKSHA\s+SANHITA', 'Bharatiya Nagarik Suraksha Sanhita, 2023', 'BNSS'),
        (r'BHARATIYA\s+SAKSHYA\s+ADHINIYAM', 'Bharatiya Sakshya Adhiniyam, 2023', 'BSA'),
        (r'INFORMATION\s+TECHNOLOGY\s+ACT', 'INFORMATION TECHNOLOGY Act, 2000', 'I_T_Act'),
        (r'INDIAN\s+TELEGRAPH\s+ACT', 'INDIAN TELEGRAPH Act, 1885', 'I_T_Act'),
        (r'RIGHT\s+TO\s+INFORMATION\s+ACT', 'Right to Information Act, 2005', 'RTI'),
        (r'THE\s+AADHAAR.*ACT,\s*2016', 'The Aadhaar Act, 2016', 'Aadhaar_Act'),
        (r'(TAMIL\s+NADU\s+.*?ACT)', None, None),  # Catch-all for TN Acts (dynamic)
    ]
    
    # Normalize text for better matching (replace newlines with spaces)
    normalized_text = ' '.join(first_pages_text.split())

    matches = []
    
    for pattern, name, short in act_patterns:
        # Detect ALL matches
        # Use simple finding on normalized text first
        for match in re.finditer(pattern, normalized_text, re.IGNORECASE):
            # If name is None (dynamic), use the matched text
            final_name = name if name else match.group(1).title()
            final_short = short if short else "".join([w[0] for w in final_name.split() if w[0].isupper()]) + "_Act"
            matches.append((match.start(), final_name, final_short))
            
    if matches:
        # Return the match that appears EARLIEST in the text
        matches.sort(key=lambda x: x[0])
        return matches[0][1], matches[0][2]

    return "Unknown Act", "Unknown"


def detect_parsing_mode(pages: List[Tuple[int, str]]) -> ParsingMode:
    """
    Determine the best parsing strategy based on document content.
    """
    # Combine first 20 pages scanning for patterns
    text = "\n".join([text for _, text in pages[:20]])
    
    # Check for schedule-heavy documents (e.g. Telegraph Act)
    if "PART I" in text and "PART II" in text and "PART III" in text:
        return ParsingMode.SCHEDULE
        
    return ParsingMode.NARRATIVE


def detect_chapters(pages: List[Tuple[int, str]]) -> Dict[int, str]:
    """
    Detect chapter boundaries and names throughout the document.
    Supports both CHAPTER and PART formats, including footnote prefixes (e.g. 2[PART).
    
    Returns:
        Dict mapping page number to chapter name
    """
    chapters = {}
    
    # Multiple patterns for chapter/part headers
    # Note: Some acts use CHAPTER, others use PART (e.g., Telegraph Act)
    # Added support for footnote markers prefix (e.g. 2[PART)
    chapter_patterns = [
        # "CHAPTERV\nOF OFFENCES" (no space - common in some PDFs)
        (r'(?:^|\n)\s*CHAPTER([IVXLCDM]+)\s*\n\s*([A-Z][A-Z\s,\.\-]+?)(?=\n\d|\n[a-z]|\nO|\n$)', 'Chapter'),
        # "CHAPTER II\nOF PUNISHMENTS"
        (r'(?:^|\n)\s*CHAPTER\s+([IVXLCDM]+|\d+)\s*\n\s*([A-Z][A-Z\s,\.\-]+?)(?=\n\d|\n[a-z]|\n$)', 'Chapter'),
        # "CHAPTER II - OF PUNISHMENTS" (inline style)
        (r'(?:^|\n)\s*CHAPTER\s*([IVXLCDM]+|\d+)\s*[-—:]\s*([A-Z][A-Z\s,\.\-]+?)(?=\n|$)', 'Chapter'),
        # "Chapter 2\nGeneral Exceptions" (mixed case)
        (r'(?:^|\n)\s*Chapter\s*([IVXLCDM]+|\d+)\s*\n\s*([A-Z][A-Za-z\s,\.\-]+?)(?=\n)', 'Chapter'),
        # "PART I\nPRELIMINARY", "2[PART IIA" (Telegraph Act style with footnotes)
        (r'(?:^|\n)\s*(?:\d+\[|\[)?PART\s*([IVXLCDM]+[A-Z]*)\s*\n\s*([A-Z][A-Z\s,\.\-]+?)(?=\n)', 'Part'),
        # "PART I - PRELIMINARY" (inline style)
        (r'(?:^|\n)\s*(?:\d+\[|\[)?PART\s*([IVXLCDM]+[A-Z]*)\s*[-—:]\s*([A-Z][A-Z\s,\.\-]+?)(?=\n|$)', 'Part'),
    ]
    
    for page_num, text in pages:
        for pattern, prefix in chapter_patterns:
            matches = re.findall(pattern, text)
            for chapter_num, chapter_title in matches:
                # Clean up chapter title
                chapter_title = chapter_title.strip()
                # Remove trailing whitespace and normalize
                chapter_title = ' '.join(chapter_title.split())
                if len(chapter_title) > 5:  # Avoid false positives
                    chapter_name = f"{prefix} {chapter_num} - {chapter_title.title()}"
                    # Only set if not already set (Keep FIRST chapter found on page)
                    # This helps when multiple chapters start on one page (e.g. Part IIA and Part III)
                    if page_num not in chapters:
                        chapters[page_num] = chapter_name
    
    return chapters


def strip_margin_notes(text: str) -> str:
    """
    Remove margin notes from extracted text.
    Margin notes in Indian legal documents typically appear as:
    - Short title-like text (e.g., "Punishment for murder.")
    - Multi-line fragments broken across lines
    - Gazette headers and page markers
    
    Returns:
        Text with margin notes removed
    """
    lines = text.split('\n')
    cleaned_lines = []
    
    # Legal keywords to preserve
    legal_keywords = ['illustration', 'illustrations', 'explanation', 'explanations', 
                      'provided', 'exception', 'proviso', 'note', 'provided that']
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Skip empty lines at start, keep others
        if not stripped:
            if cleaned_lines:  # Only add if we have content
                cleaned_lines.append(line)
            continue
        
        # Skip gazette headers and page markers
        if re.search(r'THE GAZETTE OF INDIA|EXTRAORDINARY|Sec\.\s*\d+\]|_{5,}', stripped):
            continue
        
        # Skip standalone page numbers (just digits, possibly with punctuation)
        if re.match(r'^\d{1,3}$', stripped):
            continue
        
        # Check if line starts with legal keyword - ALWAYS keep these
        first_word = stripped.split()[0].lower().rstrip('.—-:') if stripped.split() else ''
        if first_word in legal_keywords:
            cleaned_lines.append(line)
            continue
        
        # Skip very short lines (1-3 words) that look like margin note fragments
        if len(stripped) < 25 and stripped:
            words = stripped.split()
            if len(words) <= 3:
                # Skip if not starting with digit or parenthesis (likely margin note)
                if not stripped[0].isdigit() and not stripped.startswith('('):
                    continue
        
        # Skip standalone title-like lines (short, title-case, <40 chars)
        # But NOT if they contain legal terms
        if len(stripped) < 40 and stripped and not stripped[0].isdigit():
            words = stripped.split()
            if len(words) <= 6:
                # Check if contains legal keywords - keep if so
                text_lower = stripped.lower()
                if any(kw in text_lower for kw in legal_keywords):
                    cleaned_lines.append(line)
                    continue
                    
                title_words = sum(1 for w in words if w and w[0].isupper() and len(w) > 1)
                if title_words >= len(words) * 0.6:
                    if stripped.endswith('.') or (stripped[-1:].isalpha()):
                        # Likely a margin note - skip
                        continue
        
        cleaned_lines.append(line)
    
    result = '\n'.join(cleaned_lines)
    
    # Fix spacing issues: "Ajoins" -> "A joins", "B.Ais" -> "B. A is"
    result = fix_spacing_issues(result)
    
    return result


def fix_spacing_issues(text: str) -> str:
    """
    Fix spacing issues in PDF-extracted text where letters run together.
    Common patterns: "Ajoins" -> "A joins", "India.Ahas" -> "India. A has"
    """
    # Pattern: Single uppercase letter followed by lowercase word (Ajoins -> A joins)
    # But only when the uppercase letter is A, B, Z (common in legal illustrations)
    text = re.sub(r'\b([ABZ])([a-z]{2,})', r'\1 \2', text)
    
    # Pattern: word.A followed by lowercase (India.Ahas -> India. A has)
    text = re.sub(r'\.([ABZ])([a-z])', r'. \1 \2', text)
    
    # Pattern: word followed immediately by single letter (house.A -> house. A)
    text = re.sub(r'([a-z])\.([ABZ])\s', r'\1. \2 ', text)
    
    return text


def find_section_boundaries(text: str) -> List[Tuple[int, str, str]]:
    """
    Find all section start positions and their identifiers.
    
    Returns:
        List of (position, section_id, section_title_hint) tuples
    """
    sections = []
    
    # Pattern for section numbers: "103.", "3A.", "Section 103", etc.
    # This matches the start of a section
    patterns = [
        # "103. (1) Whoever..." or "103. Whoever..."
        r'(?:^|\n)\s*(\d+[A-Z]?)\.\s*(?:\(1\)\s*)?(.*?)(?=\n)',
        # "1[6A. Title..." (Sections with amendment footnotes like 1[, 2[ etc.)
        r'(?:^|\n)\s*(?:\d+\[|\[)(\d+[A-Z]?)\.\s*(?:\(1\)\s*)?(.*?)(?=\n)',
        # "Section 103. Whoever..."
        r'(?:^|\n)\s*Section\s+(\d+[A-Z]?)\.\s*(.*?)(?=\n)',
    ]
    
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.MULTILINE):
            section_id = match.group(1)
            hint = match.group(2)[:50] if len(match.groups()) > 1 else ""
            sections.append((match.start(), section_id, hint))
    
    # Sort by position
    sections.sort(key=lambda x: x[0])
    
    # Filter out likely page numbers (section_id < 4 chars, hint looks like page header)
    filtered = []
    for pos, sec_id, hint in sections:
        # Skip if section_id is just 1-2 digits and hint is empty or very short (likely page number)
        if len(sec_id) <= 2 and sec_id.isdigit() and len(hint.strip()) < 10:
            continue
            
        # Skip Digital Signature artifacts (OIDs like 2.5.4.20=...)
        # Often detected as "Section 2"
        if sec_id.isdigit() and hint.strip().startswith("5.4.20=") or "2.5.4.20=" in hint:
            continue
        filtered.append((pos, sec_id, hint))
    
    # For duplicates, keep the LAST occurrence (actual content, not TOC entry)
    # Reverse iterate to find last occurrence of each section_id
    seen = set()
    unique_sections = []
    for pos, sec_id, hint in reversed(filtered):
        if sec_id not in seen:
            seen.add(sec_id)
            unique_sections.append((pos, sec_id, hint))
    
    # Reverse back to original order
    unique_sections.reverse()
    
    return unique_sections


def has_pattern(text: str, pattern_type: str) -> bool:
    """Check if text contains specific patterns"""
    patterns = {
        "illustration": r'Illustration[s]?\.?\s*[-—]?',
        "explanation": r'Explanation[s]?\s*[\d\-—\.]*[-—]?',
        "proviso": r'Provided\s+that',
    }
    
    if pattern_type in patterns:
        return bool(re.search(patterns[pattern_type], text, re.IGNORECASE))
    return False
