"""
Script to find anomalies in processed chunks for specific Acts.
Checks for:
- Missing chapters
- Short content (potential TOC or noise)
- Header/Footer leakage
- Section gaps (e.g. 1, 3 -> missing 2)
"""
import json
import re
import os

FILES_TO_CHECK = [
    'engaadhaar_Central_act',
    'informatio_act_central',
    'the_tamil_nadu_laws_(special_provisions)_act,_2007',
    'TN_money_lenders_act_state',
    'TN_Motor_Act_spl_state'
]

def check_file(filename):
    filepath = f"scripts/poc_chunks/{filename}_chunks.json"
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    print(f"\n{'='*60}")
    print(f"Checking: {filename}")
    print(f"{'='*60}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return

    chunks = data.get('chunks', [])
    if not chunks:
        print("No chunks found!")
        return

    # 1. Check for Chapter assignments
    chunks_without_chapter = [c['metadata']['section_id'] for c in chunks if not c['metadata'].get('chapter') or c['metadata']['chapter'] == 'N/A']
    if chunks_without_chapter:
        print(f"WARNING: {len(chunks_without_chapter)} sections have no assigned Chapter.")
        if len(chunks_without_chapter) < 10:
            print(f"  Sections: {chunks_without_chapter}")

    # 2. Check for short content (noise/TOC)
    short_chunks = [c for c in chunks if len(c['raw_content'].split()) < 15]
    if short_chunks:
        print(f"WARNING: {len(short_chunks)} chunks have < 15 words (potential noise).")
        for c in short_chunks[:3]:
            print(f"  Sec {c['metadata']['section_id']}: {repr(c['raw_content'])}")

    # 3. Check for Header/Footer leakage
    header_keywords = ["GAZETTE", "EXTRAORDINARY", "PAGE", "HTTP"]
    leaky_chunks = []
    for c in chunks:
        for kw in header_keywords:
            if kw in c['raw_content'].upper().split('\n')[:3] or kw in c['raw_content'].upper().split('\n')[-3:]:
                 leaky_chunks.append(c['metadata']['section_id'])
                 break
    
    if leaky_chunks:
        print(f"WARNING: {len(leaky_chunks)} chunks may contain headers/footers.")
        # print(f"  Sections: {leaky_chunks[:5]}...")

    # 4. Check for Section Gaps
    # Extract numeric part of section IDs
    sec_nums = []
    for c in chunks:
        sid = c['metadata']['section_id']
        # Extract leading digits
        match = re.match(r'^(\d+)', sid)
        if match:
            sec_nums.append(int(match.group(1)))
    
    sec_nums = sorted(list(set(sec_nums)))
    if sec_nums:
        gaps = []
        for i in range(len(sec_nums)-1):
            if sec_nums[i+1] - sec_nums[i] > 1:
                # Check if it's a huge gap (like jumping to 100) or small gap
                if sec_nums[i+1] - sec_nums[i] < 5: 
                    gaps.append(f"{sec_nums[i]}->{sec_nums[i+1]}")
        
        if gaps:
            print(f"WARNING: Potential section gaps detected: {gaps[:10]}")

    print(f"Total Chunks: {len(chunks)}")

if __name__ == "__main__":
    for f in FILES_TO_CHECK:
        check_file(f)
