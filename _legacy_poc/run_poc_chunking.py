"""
POC Script to run chunking on all sample PDFs
Outputs results to console and JSON files
"""
import os
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.parser.manager import ParserManager
from app.parser.models import DocumentResult


def run_poc(pdf_dir: str, output_dir: str):
    """
    Run POC chunking on all PDFs in a directory.
    
    Args:
        pdf_dir: Directory containing PDF files
        output_dir: Directory to save JSON results
    """
    pdf_dir = Path(pdf_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize parser
    manager = ParserManager()
    
    # Get all PDF files
    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    
    print("=" * 80)
    print("LEGAL DOCUMENT CHUNKING POC")
    print("=" * 80)
    print(f"\nFound {len(pdf_files)} PDF files in {pdf_dir}")
    print()
    
    # Summary statistics
    total_chunks = 0
    results_summary = []
    
    for pdf_file in pdf_files:
        print(f"\n{'='*60}")
        print(f"📄 Processing: {pdf_file.name}")
        print("=" * 60)
        
        # Process PDF
        result = manager.process_pdf(str(pdf_file))
        
        # Print summary
        print(f"  Act Name: {result.act_name}")
        print(f"  Short Name: {result.act_short}")
        print(f"  Parsing Mode: {result.parsing_mode.value}")
        print(f"  Total Pages: {result.total_pages}")
        print(f"  Chunks Extracted: {result.total_chunks}")
        
        if result.errors:
            print(f"  ⚠️  Errors: {result.errors}")
        
        # Show sample chunks
        if result.chunks:
            print(f"\n  📋 Sample Chunks (first 3):")
            for i, chunk in enumerate(result.chunks[:3]):
                print(f"\n  --- Chunk {i+1}: {chunk.chunk_id} ---")
                print(f"  Section: {chunk.metadata.section_id}")
                print(f"  Chapter: {chunk.metadata.chapter or 'N/A'}")
                print(f"  Has Illustration: {chunk.metadata.has_illustration}")
                print(f"  Has Explanation: {chunk.metadata.has_explanation}")
                print(f"  Has Proviso: {chunk.metadata.has_proviso}")
                print(f"  Pages: {chunk.metadata.page_start}-{chunk.metadata.page_end}")
                # Show first 200 chars of content
                content_preview = chunk.raw_content[:200].replace('\n', ' ')
                print(f"  Content Preview: {content_preview}...")
        
        # Save to JSON
        output_file = output_dir / f"{pdf_file.stem}_chunks.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(), f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n  ✅ Saved to: {output_file}")
        
        # Update totals
        total_chunks += result.total_chunks
        results_summary.append({
            "filename": result.filename,
            "act_name": result.act_name,
            "parsing_mode": result.parsing_mode.value,
            "total_pages": result.total_pages,
            "total_chunks": result.total_chunks,
            "errors": len(result.errors)
        })
    
    # Print final summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nTotal PDFs Processed: {len(pdf_files)}")
    print(f"Total Chunks Extracted: {total_chunks}")
    
    print("\n📊 Results by Document:")
    print(f"{'Filename':<45} {'Mode':<12} {'Pages':<8} {'Chunks':<8}")
    print("-" * 75)
    for r in results_summary:
        print(f"{r['filename']:<45} {r['parsing_mode']:<12} {r['total_pages']:<8} {r['total_chunks']:<8}")
    
    # Save summary
    summary_file = output_dir / "poc_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump({
            "total_pdfs": len(pdf_files),
            "total_chunks": total_chunks,
            "results": results_summary
        }, f, indent=2)
    
    print(f"\n✅ Summary saved to: {summary_file}")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    # Default paths
    pdf_dir = "Sample_pdf"
    output_dir = "scripts/poc_chunks"
    
    # Allow command line override
    if len(sys.argv) > 1:
        pdf_dir = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    
    run_poc(pdf_dir, output_dir)
