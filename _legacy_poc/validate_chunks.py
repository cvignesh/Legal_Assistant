"""
Validation script to check chunk quality across ALL PDFs
"""
import json
import random
import os

def validate_pdf(filename, display_name):
    filepath = f'scripts/poc_chunks/{filename}_chunks.json'
    if not os.path.exists(filepath):
        print(f"SKIPPED: {filepath} not found")
        return []
        
    print('=' * 70)
    print(f'{display_name} VALIDATION')
    print('=' * 70)
    
    d = json.load(open(filepath, encoding='utf-8'))
    
    # Random samples
    random.seed(42)
    sample_count = min(4, len(d['chunks']))
    if sample_count == 0:
        print("  No chunks found!")
        return []
        
    samples = random.sample(d['chunks'], sample_count)
    
    all_issues = []
    
    for chunk in samples:
        m = chunk['metadata']
        content = chunk['raw_content']
        
        print(f"\nSection {m['section_id']} | Chapter: {m['chapter'] or 'N/A'}")
        
        issues = []
        
        # Check for headers
        if 'GAZETTE' in content.upper():
            issues.append('HEADER')
            
        # Check for underlines
        if '____' in content:
            issues.append('UNDERLINES')
            
        # Check for spacing issues
        import re
        if re.search(r'\b[ABZ][a-z]{4,}', content):
            # Check if it's a valid word
            matches = re.findall(r'\b[ABZ][a-z]{4,}', content)
            bad = [m for m in matches if m.lower() not in ['about', 'above', 'against', 'before', 'being', 'below', 'between', 'beyond', 'after', 'along', 'among', 'around', 'behalf', 'body', 'bail', 'bailable', 'bank', 'banking']]
            if bad:
                issues.append(f'SPACING?:{bad[:2]}')
        
        print(f"  Issues: {issues if issues else 'NONE ✓'}")
        print(f"  Preview: {content[:100]}...")
        
        all_issues.extend(issues)
    
    print(f"\n  TOTAL ISSUES: {len(all_issues)}")
    return all_issues

# Run validation on all PDFs
print("\n" + "="*70)
print("VALIDATING ALL REMAINING ACTS")
print("="*70 + "\n")

results = {}

# Remaining 7 acts
pdfs = [
    ('engaadhaar_Central_act', 'Aadhaar Act'),
    ('indiantelegraphact_1885', 'Indian Telegraph Act'),
    ('informatio_act_central', 'RTI Act (informatio)'),
    ('it_act_2000_updated', 'IT Act 2000'),
    ('the_tamil_nadu_laws_(special_provisions)_act,_2007', 'TN Laws Special'),
    ('TN_money_lenders_act_state', 'TN Money Lenders'),
    ('TN_Motor_Act_spl_state', 'TN Motor Act'),
]

total_issues = 0
for filename, display in pdfs:
    issues = validate_pdf(filename, display)
    results[display] = len(issues)
    total_issues += len(issues)

# Summary
print("\n" + "="*70)
print("FINAL SUMMARY - REMAINING ACTS")
print("="*70)
for name, count in results.items():
    status = "✓" if count == 0 else f"⚠ {count} issues"
    print(f"  {name}: {status}")
print(f"\nTOTAL ISSUES: {total_issues}")
