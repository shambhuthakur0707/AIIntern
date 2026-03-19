"""
Clear all match results from user profiles in the database.
Run from backend directory: python clear_match_results.py
Use --force flag to skip confirmation: python clear_match_results.py --force
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

def clear_match_results(force=False):
    """Clear all match results from user profiles."""
    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_URI)
        db = client[MONGO_DB_NAME]
        
        # Get current count of users with match results
        users_with_results = db.users.count_documents({"last_match_result": {"$exists": True, "$ne": None}})
        print(f"📊 Users with match results: {users_with_results}")
        
        if users_with_results == 0:
            print("✓ No match results to clear.")
            client.close()
            return
        
        # Confirm deletion (unless --force flag used)
        if not force:
            confirm = input(f"\n⚠️  Clear match results for ALL {users_with_results} user(s)? (yes/no): ").strip().lower()
            if confirm != "yes":
                print("❌ Operation cancelled.")
                client.close()
                return
        else:
            print(f"\n⚠️  Clearing match results for {users_with_results} user(s)...")
        
        # Clear match results from all users
        result = db.users.update_many(
            {"last_match_result": {"$exists": True}},
            {"$set": {"last_match_result": None}}
        )
        print(f"✓ Updated {result.modified_count} user profile(s)!")
        
        # Verify
        remaining = db.users.count_documents({"last_match_result": {"$exists": True, "$ne": None}})
        print(f"\n📊 Users with match results remaining: {remaining}")
        
        client.close()
        print("\n✅ Clear complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    force_delete = "--force" in sys.argv
    print("=" * 60)
    print("MATCH RESULTS CLEANUP TOOL")
    print("=" * 60)
    clear_match_results(force=force_delete)
