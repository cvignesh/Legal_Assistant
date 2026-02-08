#!/usr/bin/env python3
"""
Backfill script: populate `metadata.case_id` from `metadata.case_number` for existing chunks.

Usage:
  python backfill_case_id.py --mongo-uri "$MONGO_URI" --db mydb --collection legal_chunks_v1 --dry-run

If --apply is passed, performs the update. Otherwise shows counts and sample.
"""
import argparse
import os
from pymongo import MongoClient


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mongo-uri", help="MongoDB connection string", default=os.environ.get("MONGO_URI"))
    p.add_argument("--db", help="Database name", default=os.environ.get("MONGO_DB") or "legal_assistant")
    p.add_argument("--collection", help="Collection name", default=os.environ.get("MONGO_COLLECTION_CHUNKS") or "legal_chunks_v1")
    p.add_argument("--apply", help="Perform the update (default: dry-run)", action="store_true")
    p.add_argument("--sample", help="Show sample docs (n)", type=int, default=3)
    args = p.parse_args()

    if not args.mongo_uri:
        print("ERROR: Mongo URI not provided. Set MONGO_URI env or pass --mongo-uri")
        return

    client = MongoClient(args.mongo_uri)
    db = client[args.db]
    coll = db[args.collection]

    total = coll.count_documents({})
    have_case_number = coll.count_documents({"metadata.case_number": {"$exists": True, "$ne": None, "$ne": ""}})
    have_case_id = coll.count_documents({"metadata.case_id": {"$exists": True, "$ne": None, "$ne": ""}})
    need_update = coll.count_documents({"$or": [
        {"metadata.case_id": {"$exists": False}},
        {"metadata.case_id": None},
        {"metadata.case_id": ""}
    ], "metadata.case_number": {"$exists": True, "$ne": None, "$ne": ""}})

    print(f"Collection: {args.db}.{args.collection}")
    print(f"Total documents: {total}")
    print(f"Have metadata.case_number: {have_case_number}")
    print(f"Have metadata.case_id: {have_case_id}")
    print(f"Documents needing update (case_number -> case_id): {need_update}\n")

    if need_update == 0:
        print("No documents require update. Exiting.")
        return

    print("Sample documents needing update:")
    for doc in coll.find({"$or": [
        {"metadata.case_id": {"$exists": False}},
        {"metadata.case_id": None},
        {"metadata.case_id": ""}
    ], "metadata.case_number": {"$exists": True, "$ne": None, "$ne": ""}}, {"metadata.case_number":1, "metadata.case_id":1}) .limit(args.sample):
        print(doc)

    if not args.apply:
        print("\nDry run. To apply changes, re-run with --apply")
        return

    # Perform update using aggregation pipeline (MongoDB 4.2+)
    filter_q = {"$or": [
        {"metadata.case_id": {"$exists": False}},
        {"metadata.case_id": None},
        {"metadata.case_id": ""}
    ], "metadata.case_number": {"$exists": True, "$ne": None, "$ne": ""}}

    update_pipeline = [{"$set": {"metadata.case_id": {"$trim": {"input": "$metadata.case_number"}}}}]

    result = coll.update_many(filter_q, update_pipeline)
    print(f"Matched: {result.matched_count}, Modified: {result.modified_count}")

    # Verify
    have_case_id_after = coll.count_documents({"metadata.case_id": {"$exists": True, "$ne": None, "$ne": ""}})
    print(f"Documents with metadata.case_id after update: {have_case_id_after}")


if __name__ == '__main__':
    main()
