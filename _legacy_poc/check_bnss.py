"""Find FIRST SCHEDULE table in BNSS - check all pages for offence classification table"""
import pdfplumber

pdf = pdfplumber.open('Sample_pdf/BNSS.pdf')
print(f'Total pages: {len(pdf.pages)}')

# Look for pattern keywords typical in BNSS schedule: Cognizable, Bailable, etc
for i in range(len(pdf.pages)):
    text = pdf.pages[i].extract_text() or ''
    # Table header keywords
    if ('Cognizable' in text and 'Bailable' in text) or \
       ('FIRST SCHEDULE' in text.upper() and 'Offence' in text):
        print(f'\n=== Page {i+1} - SCHEDULE TABLE FOUND ===')
        print(text[:4000])
        print('\n--- Next page ---')
        if i+1 < len(pdf.pages):
            print(pdf.pages[i+1].extract_text()[:3000])
        break
else:
    print("FIRST SCHEDULE table not found in text. May be a scanned image.")
    # Check middle pages
    print("\n=== Checking middle pages (around 130-140) for Schedule ===")
    for i in range(128, 145):
        text = pdf.pages[i].extract_text() or ''
        print(f'\n--- Page {i+1} ---')
        print(text[:2000])

pdf.close()
