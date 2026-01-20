"""
PDF Analysis Script for Legal Assistant POC
Analyzes all sample PDFs to categorize them by parsing mode (Narrative/Strict/Schedule)
"""
import pdfplumber
import os
import re
import json

def analyze_pdf(filepath):
    """Analyze a PDF and detect patterns for categorization"""
    pdf = pdfplumber.open(filepath)
    total_pages = len(pdf.pages)
    
    # Extract text from first 20 pages (or all if fewer)
    sample_pages = min(20, total_pages)
    all_text = ''
    
    char_counts = []
    spacing_issues_pages = []
    
    for i in range(sample_pages):
        text = pdf.pages[i].extract_text() or ''
        char_counts.append(len(text))
        all_text += text + '\n'
        
        # Check for spacing issues (words without spaces - 25+ chars in a row)
        long_words = re.findall(r'[a-zA-Z]{25,}', text)
        if long_words:
            spacing_issues_pages.append(i + 1)  # 1-indexed
    
    # Pattern detection
    illustrations = len(re.findall(r'Illustration[s]?\.?', all_text, re.IGNORECASE))
    explanations = len(re.findall(r'Explanation[s]?\s*[\d\-—\.]*', all_text, re.IGNORECASE))
    provisos = len(re.findall(r'Provided\s+that', all_text, re.IGNORECASE))
    schedules = len(re.findall(r'(THE\s+SCHEDULE|FIRST\s+SCHEDULE|SECOND\s+SCHEDULE|SCHEDULE\s+[IVX]+)', all_text, re.IGNORECASE))
    sections = len(re.findall(r'^\d+[A-Z]?\.\s', all_text, re.MULTILINE))
    chapters = len(re.findall(r'CHAPTER\s+[IVXLCDM\d]+', all_text, re.IGNORECASE))
    
    # Check last 5 pages for schedule/forms
    last_pages_text = ''
    for i in range(max(0, total_pages-5), total_pages):
        last_pages_text += (pdf.pages[i].extract_text() or '') + '\n'
    has_forms = 'FORM No.' in last_pages_text or 'FORM NO.' in last_pages_text
    has_schedule_table = bool(re.search(r'(Cognizable|Non-cognizable|Bailable|Non-bailable)', last_pages_text))
    
    pdf.close()
    
    return {
        'total_pages': total_pages,
        'sample_pages': sample_pages,
        'avg_chars': sum(char_counts) / len(char_counts) if char_counts else 0,
        'illustrations': illustrations,
        'explanations': explanations,
        'provisos': provisos,
        'schedules': schedules,
        'sections': sections,
        'chapters': chapters,
        'spacing_issues_pages': spacing_issues_pages,
        'has_spacing_issues': len(spacing_issues_pages) > 0,
        'has_forms': has_forms,
        'has_schedule_table': has_schedule_table
    }

def categorize_pdf(stats):
    """Determine recommended parsing mode based on patterns"""
    if stats['illustrations'] >= 5 or stats['explanations'] >= 5:
        mode = 'NARRATIVE'
        reason = f"Illustrations:{stats['illustrations']}, Explanations:{stats['explanations']}"
    elif stats['provisos'] >= 10:
        mode = 'STRICT'
        reason = f"Provisos:{stats['provisos']}"
    elif stats['schedules'] >= 1 or stats['has_schedule_table']:
        mode = 'SCHEDULE'
        reason = f"Schedules:{stats['schedules']}, HasTable:{stats['has_schedule_table']}"
    elif stats['provisos'] >= 3:
        mode = 'STRICT'
        reason = f"Provisos:{stats['provisos']} (moderate)"
    else:
        mode = 'NARRATIVE'
        reason = 'Default - no strong pattern detected'
    
    return mode, reason

def main():
    pdf_dir = 'Sample_pdf'
    results = []
    
    print("=" * 80)
    print("PDF ANALYSIS FOR LEGAL ASSISTANT CHUNKING POC")
    print("=" * 80)
    
    for filename in sorted(os.listdir(pdf_dir)):
        if filename.lower().endswith('.pdf'):
            filepath = os.path.join(pdf_dir, filename)
            print(f'\n{"="*60}')
            print(f'📄 {filename}')
            print("="*60)
            
            try:
                stats = analyze_pdf(filepath)
                mode, reason = categorize_pdf(stats)
                
                print(f'  Pages: {stats["total_pages"]} | Avg chars/page: {stats["avg_chars"]:.0f}')
                print(f'  Chapters: {stats["chapters"]} | Sections detected: {stats["sections"]}')
                print(f'  Illustrations: {stats["illustrations"]} | Explanations: {stats["explanations"]}')
                print(f'  Provisos: {stats["provisos"]} | Schedules: {stats["schedules"]}')
                print(f'  Has Forms: {stats["has_forms"]} | Has Schedule Table: {stats["has_schedule_table"]}')
                
                # Spacing issues detail
                if stats['has_spacing_issues']:
                    print(f'  ⚠️  SPACING ISSUES on pages: {stats["spacing_issues_pages"][:10]}{"..." if len(stats["spacing_issues_pages"]) > 10 else ""}')
                else:
                    print(f'  ✅ No spacing issues detected')
                
                print(f'\n  >>> RECOMMENDED MODE: {mode}')
                print(f'  >>> Reason: {reason}')
                
                # Store result
                results.append({
                    'filename': filename,
                    'recommended_mode': mode,
                    'reason': reason,
                    'has_spacing_issues': stats['has_spacing_issues'],
                    'spacing_issues_sample_pages': stats['spacing_issues_pages'][:5] if stats['spacing_issues_pages'] else [],
                    'stats': {
                        'total_pages': stats['total_pages'],
                        'chapters': stats['chapters'],
                        'sections': stats['sections'],
                        'illustrations': stats['illustrations'],
                        'explanations': stats['explanations'],
                        'provisos': stats['provisos'],
                        'schedules': stats['schedules'],
                        'has_forms': stats['has_forms'],
                        'has_schedule_table': stats['has_schedule_table']
                    }
                })
                
            except Exception as e:
                print(f'  ❌ ERROR: {e}')
                results.append({
                    'filename': filename,
                    'error': str(e)
                })
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY - PARSING MODE RECOMMENDATIONS")
    print("=" * 80)
    
    mode_groups = {'NARRATIVE': [], 'STRICT': [], 'SCHEDULE': []}
    spacing_issues_files = []
    
    for r in results:
        if 'error' not in r:
            mode_groups[r['recommended_mode']].append(r['filename'])
            if r['has_spacing_issues']:
                spacing_issues_files.append(r['filename'])
    
    print("\n📗 NARRATIVE Mode (Illustrations/Explanations):")
    for f in mode_groups['NARRATIVE']:
        print(f"   - {f}")
    
    print("\n📘 STRICT Mode (Provisos):")
    for f in mode_groups['STRICT']:
        print(f"   - {f}")
    
    print("\n📙 SCHEDULE Mode (Tables):")
    for f in mode_groups['SCHEDULE']:
        print(f"   - {f}")
    
    print("\n⚠️  FILES WITH SPACING ISSUES (may need special handling):")
    for f in spacing_issues_files:
        print(f"   - {f}")
    
    # Save to JSON
    output_path = 'scripts/pdf_analysis_results.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Results saved to: {output_path}")

if __name__ == '__main__':
    main()
