#!/usr/bin/env python3
"""
Test script for Food Premi MongoDB connection
Run this to verify your database connection is working
"""

from database import db_connection

def test_connection():
    print("Testing MongoDB connection...")
    print("-" * 50)
    
    # Test connection
    if db_connection.connect():
        db = db_connection.get_database()
        
        # Test basic operations
        try:
            # List collections
            collections = db.list_collection_names()
            print(f"Available collections: {collections}")
            
            # Test inserting a document
            test_collection = db.test_collection
            test_doc = {
                "test": True,
                "message": "Food Premi DB connection successful!",
                "timestamp": "2025-01-16"
            }
            
            result = test_collection.insert_one(test_doc)
            print(f"Test document inserted with ID: {result.inserted_id}")
            
            # Test reading the document
            found_doc = test_collection.find_one({"_id": result.inserted_id})
            print(f"Retrieved document: {found_doc}")
            
            # Clean up test document
            test_collection.delete_one({"_id": result.inserted_id})
            print("Test document cleaned up")
            
            print("\nAll database operations successful!")
            
        except Exception as e:
            print(f"Error during database operations: {e}")
            
        finally:
            db_connection.close_connection()
    
    else:
        print("Failed to connect to database")

if __name__ == "__main__":
    test_connection()