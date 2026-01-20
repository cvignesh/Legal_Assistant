"""
Parsing strategies for different types of legal documents
"""
import re
from typing import List, Tuple, Dict, Optional
from abc import ABC, abstractmethod

from .models import LegalChunk, ChunkMetadata, ChunkType, ParsingMode
from .utils import has_pattern, find_section_boundaries, strip_margin_notes


class BaseStrategy(ABC):
    """Base class for parsing strategies"""
    
    def __init__(self, act_name: str, act_short: str, chapters: Dict[int, str]):
        self.act_name = act_name
        self.act_short = act_short
        self.chapters = chapters  # page_num -> chapter_name
        self.current_chapter = None
    
    def get_chapter_for_page(self, page_num: int) -> Optional[str]:
        """Get the current chapter for a given page number"""
        # Find the most recent chapter before or on this page
        applicable_chapters = [(p, c) for p, c in self.chapters.items() if p <= page_num]
        if applicable_chapters:
            # Get the chapter from the highest page number <= page_num
            return max(applicable_chapters, key=lambda x: x[0])[1]
        return self.current_chapter
    
    def update_chapter(self, page_num: int, text: str):
        """Update current chapter if a new chapter header is found"""
        chapter = self.get_chapter_for_page(page_num)
        if chapter:
            self.current_chapter = chapter
    
    @abstractmethod
    def parse(self, pages: List[Tuple[int, str]]) -> List[LegalChunk]:
        """Parse pages and return list of chunks"""
        pass
    
    def create_chunk(
        self,
        section_id: str,
        raw_content: str,
        page_start: int,
        page_end: int,
        section_title: Optional[str] = None,
        chunk_type: ChunkType = ChunkType.SECTION
    ) -> LegalChunk:
        """Create a LegalChunk with proper enrichment"""
        
        # Detect patterns in content
        has_illustration = has_pattern(raw_content, "illustration")
        has_explanation = has_pattern(raw_content, "explanation")
        has_proviso = has_pattern(raw_content, "proviso")
        
        # Build enriched text for embedding
        context_parts = [f"[{self.act_short}]"]
        if self.current_chapter:
            context_parts.append(f"[{self.current_chapter}]")
        context_parts.append(f"Section {section_id}")
        
        text_for_embedding = " > ".join(context_parts) + " : " + raw_content.strip()
        
        # Create chunk ID
        chunk_id = f"{self.act_short}_Sec_{section_id}"
        
        return LegalChunk(
            chunk_id=chunk_id,
            text_for_embedding=text_for_embedding,
            raw_content=raw_content.strip(),
            metadata=ChunkMetadata(
                act_name=self.act_name,
                act_short=self.act_short,
                chapter=self.current_chapter,
                section_id=section_id,
                section_title=section_title,
                chunk_type=chunk_type,
                has_illustration=has_illustration,
                has_explanation=has_explanation,
                has_proviso=has_proviso,
                page_start=page_start,
                page_end=page_end
            )
        )


class NarrativeStrategy(BaseStrategy):
    """
    Strategy for acts with Illustrations and Explanations.
    Attaches Illustrations/Explanations to their parent Section.
    Used for: BNS, BSA, IT Act, etc.
    """
    
    def parse(self, pages: List[Tuple[int, str]]) -> List[LegalChunk]:
        chunks = []
        
        # Combine all text with page tracking
        full_text = ""
        page_boundaries = []  # (start_pos, page_num)
        
        for page_num, text in pages:
            self.update_chapter(page_num, text)
            page_boundaries.append((len(full_text), page_num))
            full_text += text + "\n"
        
        # Find all section boundaries
        sections = find_section_boundaries(full_text)
        
        if not sections:
            return chunks
        
        # Extract each section with its content
        for i, (pos, section_id, hint) in enumerate(sections):
            # Determine end position (start of next section or end of text)
            if i + 1 < len(sections):
                end_pos = sections[i + 1][0]
            else:
                end_pos = len(full_text)
            
            # Extract raw content and strip margin notes
            raw_content = full_text[pos:end_pos].strip()
            raw_content = strip_margin_notes(raw_content)
            
            # Skip if too short (likely a false positive)
            if len(raw_content) < 50:
                continue
            
            # Find page numbers for this section
            page_start = 1
            page_end = 1
            for boundary_pos, page_num in page_boundaries:
                if boundary_pos <= pos:
                    page_start = page_num
                if boundary_pos <= end_pos:
                    page_end = page_num
            
            # Update current chapter based on section position
            self.update_chapter(page_start, "")
            
            # Create chunk (Illustrations/Explanations are included in raw_content)
            chunk = self.create_chunk(
                section_id=section_id,
                raw_content=raw_content,
                page_start=page_start,
                page_end=page_end
            )
            
            chunks.append(chunk)
        
        return chunks


class StrictStrategy(BaseStrategy):
    """
    Strategy for acts with Provisos.
    Attaches "Provided that..." clauses to their parent Section.
    Used for: TN Money Lenders Act, Income Tax Act, etc.
    """
    
    def parse(self, pages: List[Tuple[int, str]]) -> List[LegalChunk]:
        # Implementation is similar to Narrative - provisos are naturally attached
        # The main difference is in pattern detection during chunk creation
        
        chunks = []
        full_text = ""
        page_boundaries = []
        
        for page_num, text in pages:
            self.update_chapter(page_num, text)
            page_boundaries.append((len(full_text), page_num))
            full_text += text + "\n"
        
        sections = find_section_boundaries(full_text)
        
        if not sections:
            return chunks
        
        for i, (pos, section_id, hint) in enumerate(sections):
            if i + 1 < len(sections):
                end_pos = sections[i + 1][0]
            else:
                end_pos = len(full_text)
            
            raw_content = full_text[pos:end_pos].strip()
            raw_content = strip_margin_notes(raw_content)
            
            if len(raw_content) < 50:
                continue
            
            page_start = 1
            page_end = 1
            for boundary_pos, page_num in page_boundaries:
                if boundary_pos <= pos:
                    page_start = page_num
                if boundary_pos <= end_pos:
                    page_end = page_num
            
            self.update_chapter(page_start, "")
            
            chunk = self.create_chunk(
                section_id=section_id,
                raw_content=raw_content,
                page_start=page_start,
                page_end=page_end
            )
            
            chunks.append(chunk)
        
        return chunks


class ScheduleStrategy(BaseStrategy):
    """
    Strategy for documents with tabular schedules.
    Parses schedule tables row-by-row.
    Used for: BNSS First Schedule, Telegraph Act, PMLA, etc.
    """
    
    def parse(self, pages: List[Tuple[int, str]]) -> List[LegalChunk]:
        chunks = []
        
        # First, parse regular sections (before schedule)
        regular_chunks = self._parse_regular_sections(pages)
        chunks.extend(regular_chunks)
        
        # Then, find and parse schedule tables
        schedule_chunks = self._parse_schedules(pages)
        chunks.extend(schedule_chunks)
        
        return chunks
    
    def _parse_regular_sections(self, pages: List[Tuple[int, str]]) -> List[LegalChunk]:
        """Parse regular sections before the schedule"""
        chunks = []
        full_text = ""
        page_boundaries = []
        
        # Find where SCHEDULE starts
        schedule_start_page = None
        for page_num, text in pages:
            if re.search(r'(?:^|\n)\s*(THE\s+FIRST\s+SCHEDULE|FIRST\s+SCHEDULE|THE\s+SCHEDULE|SECOND\s+SCHEDULE)\s*(?=\n|$)', text, re.IGNORECASE):
                schedule_start_page = page_num
                break
            page_boundaries.append((len(full_text), page_num))
            full_text += text + "\n"
        
        if not full_text:
            return chunks
        
        sections = find_section_boundaries(full_text)
        
        for i, (pos, section_id, hint) in enumerate(sections):
            if i + 1 < len(sections):
                end_pos = sections[i + 1][0]
            else:
                end_pos = len(full_text)
            
            raw_content = full_text[pos:end_pos].strip()
            
            if len(raw_content) < 50:
                continue
            
            page_start = 1
            page_end = 1
            for boundary_pos, page_num in page_boundaries:
                if boundary_pos <= pos:
                    page_start = page_num
                if boundary_pos <= end_pos:
                    page_end = page_num
            
            self.update_chapter(page_start, "")
            
            chunk = self.create_chunk(
                section_id=section_id,
                raw_content=raw_content,
                page_start=page_start,
                page_end=page_end
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def _parse_schedules(self, pages: List[Tuple[int, str]]) -> List[LegalChunk]:
        """Parse schedule tables row-by-row"""
        chunks = []
        in_schedule = False
        schedule_name = "First Schedule"
        
        for page_num, text in pages:
            # Check for schedule start
            schedule_match = re.search(
                r'(?:^|\n)\s*(THE\s+FIRST\s+SCHEDULE|FIRST\s+SCHEDULE|THE\s+SCHEDULE|SECOND\s+SCHEDULE)\s*(?=\n|$)',
                text, re.IGNORECASE
            )
            if schedule_match:
                in_schedule = True
                schedule_name = schedule_match.group(1).title().replace("The ", "")
            
            if not in_schedule:
                continue
            
            # Skip form pages
            if re.search(r'FORM\s+No\.?\s*\d+', text, re.IGNORECASE):
                continue
            
            # Parse table rows - look for section numbers at start of lines
            # Pattern for BNSS schedule: section number followed by offense description
            row_pattern = r'^(\d+[A-Za-z]?(?:\([a-z]\))?)\s+(.+?)(?=\n\d+[A-Za-z]?(?:\([a-z]\))?\s|\Z)'
            
            rows = re.findall(row_pattern, text, re.MULTILINE | re.DOTALL)
            
            for section_id, row_content in rows:
                # Clean up the row content
                row_content = ' '.join(row_content.split())  # Normalize whitespace
                
                if len(row_content) < 20:
                    continue
                
                # Create enriched text
                text_for_embedding = (
                    f"[{self.act_short}] > [{schedule_name}] > "
                    f"Section {section_id} : {row_content}"
                )
                
                chunk_id = f"{self.act_short}_Schedule_{section_id}"
                
                chunk = LegalChunk(
                    chunk_id=chunk_id,
                    text_for_embedding=text_for_embedding,
                    raw_content=row_content,
                    metadata=ChunkMetadata(
                        act_name=self.act_name,
                        act_short=self.act_short,
                        chapter=schedule_name,
                        section_id=section_id,
                        section_title=None,
                        chunk_type=ChunkType.SCHEDULE_ENTRY,
                        has_illustration=False,
                        has_explanation=False,
                        has_proviso=False,
                        page_start=page_num,
                        page_end=page_num
                    )
                )
                
                chunks.append(chunk)
        
        return chunks


def get_strategy(mode: ParsingMode, act_name: str, act_short: str, chapters: Dict[int, str]) -> BaseStrategy:
    """Factory function to get the appropriate strategy"""
    strategies = {
        ParsingMode.NARRATIVE: NarrativeStrategy,
        ParsingMode.STRICT: StrictStrategy,
        ParsingMode.SCHEDULE: ScheduleStrategy,
    }
    
    strategy_class = strategies.get(mode, NarrativeStrategy)
    return strategy_class(act_name, act_short, chapters)
