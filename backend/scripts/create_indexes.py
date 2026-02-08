"""
Utility script to create helpful MongoDB indexes for the application.

Run this from the backend folder (or ensure PYTHONPATH includes app):

    python scripts/create_indexes.py

This creates regular MongoDB indexes. NOTE: For Atlas Search (vector/$vectorSearch),
if you use Atlas Search filters on document fields (like `metadata.section`), you must
configure an Atlas Search index via the Atlas UI and include those fields in the
`mappings` for the Search index. This script only creates standard MongoDB indexes
which improve aggregation/query performance.
"""
from pymongo import MongoClient
from app.core.config import settings


def create_indexes():
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB]
    coll = db[settings.MONGO_COLLECTION_CHUNKS]

    print(f"Creating indexes on collection: {settings.MONGO_COLLECTION_CHUNKS}")

    # Compound index for metadata.section_type + metadata.case_number
    idx_name = coll.create_index([
        ("metadata.section_type", 1),
        ("metadata.case_number", 1),
    ], name="metadata_section_case_number_idx")

    print(f"Created index: {idx_name}")

    # Optional: index on embedding presence or created_at
    idx2 = coll.create_index([("created_at", -1)], name="created_at_idx")
    print(f"Created index: {idx2}")


if __name__ == "__main__":
    create_indexes()
