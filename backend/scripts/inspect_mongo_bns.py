import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

from app.db.mongo import mongo
import json

mongo.connect()
collection = mongo.db['legal_chunks_v1']

print("=== MongoDB Collection Analysis ===\n")

# Total count
total = collection.count_documents({})
print(f"Total documents: {total}\n")

# Sample document
print("=== Sample Document ===")
doc = collection.find_one()
if doc:
    # Remove embedding vector for readability
    if 'embedding' in doc:
        doc['embedding'] = f"<vector of {len(doc['embedding'])} dimensions>"
    print(json.dumps(doc, indent=2, default=str))
else:
    print("No documents found")

print("\n=== Searching for 'act' documents ===")
# Try different filter variations
filters_to_try = [
    {'extra_metadata.document_type': 'act'},
    {'document_type': 'act'},
    {'metadata.document_type': 'act'},
    {'extra_metadata.doc_type': 'act'},
]

for filter_query in filters_to_try:
    count = collection.count_documents(filter_query)
    print(f"Filter {filter_query}: {count} documents")
    if count > 0:
        sample = collection.find_one(filter_query)
        if sample and 'embedding' in sample:
            sample['embedding'] = f"<vector of {len(sample['embedding'])} dimensions>"
        print(f"Sample: {json.dumps(sample, indent=2, default=str)[:500]}...\n")
        break

print("\n=== Searching for BNS/Section 318 ===")
# Try text search
text_filters = [
    {'text_for_embedding': {'$regex': '318', '$options': 'i'}},
    {'text_for_embedding': {'$regex': 'BNS', '$options': 'i'}},
    {'text_for_embedding': {'$regex': 'Section 318', '$options': 'i'}},
]

for filter_query in text_filters:
    count = collection.count_documents(filter_query)
    print(f"Filter {filter_query}: {count} documents")
    if count > 0 and count < 10:
        samples = list(collection.find(filter_query).limit(2))
        for sample in samples:
            if 'embedding' in sample:
                sample['embedding'] = f"<vector>"
            print(f"Text preview: {sample.get('text_for_embedding', '')[:200]}...")
            print(f"Metadata: {sample.get('extra_metadata', sample.get('metadata', {}))}\n")
