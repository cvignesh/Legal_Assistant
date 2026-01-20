"""
Regression check for BNS, BNSS, BSA after IT Act fix
"""
import json

print('=' * 60)
print('REGRESSION CHECK - BNS, BNSS, BSA')
print('=' * 60)

for pdf in ['BNS', 'BNSS', 'BSA']:
    d = json.load(open(f'scripts/poc_chunks/{pdf}_chunks.json', encoding='utf-8'))
    chunks = d['chunks']
    
    print(f'\n{pdf}:')
    print(f'  Total chunks: {len(chunks)}')
    
    # Check key sections
    if pdf == 'BNS':
        sec127 = [c for c in chunks if c['metadata']['section_id'] == '127']
        sec147 = [c for c in chunks if c['metadata']['section_id'] == '147']
        sec351 = [c for c in chunks if c['metadata']['section_id'] == '351']
        print(f"  Section 127 chapter: {sec127[0]['metadata']['chapter'] if sec127 else 'MISSING!'}")
        print(f"  Section 147 has 'A joins': {'A joins' in sec147[0]['raw_content'] if sec147 else 'MISSING!'}")
        print(f"  Section 351 chapter: {sec351[0]['metadata']['chapter'] if sec351 else 'MISSING!'}")
        
    # Check for issues
    issues = 0
    for c in chunks[:20]:  # Sample first 20
        content = c['raw_content']
        if 'GAZETTE' in content.upper(): issues += 1
        if '____' in content: issues += 1
    print(f'  Issues in first 20 chunks: {issues}')
    
    # Check chapters detected
    chapters = set(c['metadata']['chapter'] for c in chunks if c['metadata']['chapter'])
    print(f'  Chapters detected: {len(chapters)}')

print('\n' + '=' * 60)
print('REGRESSION CHECK COMPLETE')
print('=' * 60)
