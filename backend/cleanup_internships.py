"""
Cleanup script to remove all internships from the database.
Run from backend directory: python cleanup_internships.py
Use --force flag to skip confirmation: python cleanup_internships.py --force
"""

import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "aiintern_db")

def clean_internships(force=False):
    """Delete all internships from the database."""
    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_URI)
        db = client[MONGO_DB_NAME]
        
        # Get current count
        count_before = db.internships.count_documents({})
        print(f"📊 Current internships in database: {count_before}")
        
        if count_before == 0:
            print("✓ Database is already empty. No internships to delete.")
            client.close()
            return
        
        # Confirm deletion (unless --force flag used)
        if not force:
            confirm = input(f"\n⚠️  Are you sure you want to delete ALL {count_before} internship(s)? (yes/no): ").strip().lower()
            if confirm != "yes":
                print("❌ Deletion cancelled.")
                client.close()
                return
        else:
            print(f"\n⚠️  Deleting ALL {count_before} internship(s)...")
        
        # Delete all internships
        result = db.internships.delete_many({})
        print(f"✓ Deleted {result.deleted_count} internship(s) successfully!")
        
        # Also clean related analyses cache
        cache_deleted = db.internship_analyses.delete_many({})
        print(f"✓ Cleaned up {cache_deleted.deleted_count} analysis cache record(s)")
        
        # Verify
        count_after = db.internships.count_documents({})
        print(f"\n📊 Internships remaining in database: {count_after}")
        
        client.close()
        print("\n✅ Cleanup complete!")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        raise

if __name__ == "__main__":
    force_delete = "--force" in sys.argv
    print("=" * 60)
    print("INTERNSHIP DATABASE CLEANUP TOOL")
    print("=" * 60)
    clean_internships(force=force_delete)
