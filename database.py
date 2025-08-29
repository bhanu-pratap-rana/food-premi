from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseConnection:
    def __init__(self):
        # Use environment variable for password, fallback to the provided one
        db_password = os.getenv('DB_PASSWORD', 'b8h9a7n9')
        
        # Working connection string with ServerApi
        self.uri = f"mongodb+srv://basant:{db_password}@foodpremi.m4l9uit.mongodb.net/?retryWrites=true&w=majority&appName=foodpremi"
        self.client = None
        self.db = None
        
    def connect(self):
        """Establish connection to MongoDB using ServerApi"""
        try:
            print("Connecting to MongoDB Atlas...")
            # Create client with ServerApi version 1
            self.client = MongoClient(self.uri, server_api=ServerApi('1'))
            
            # Test the connection with ping
            self.client.admin.command('ping')
            print("Successfully connected to MongoDB!")
            
            # Select the database
            self.db = self.client['foodpremi']
            return True
            
        except Exception as e:
            print(f"Connection failed: {str(e)}")
            if self.client:
                self.client.close()
                self.client = None
            return False
    
    def get_database(self):
        """Get the database instance"""
        if self.db is None:
            success = self.connect()
            if not success:
                print("Warning: Running in offline mode without database")
                return None
        return self.db
    
    def close_connection(self):
        """Close the database connection"""
        if self.client:
            self.client.close()
            print("Database connection closed")

# Global database instance
db_connection = DatabaseConnection()

def get_db():
    """Get database instance for use in other modules"""
    return db_connection.get_database()

# Test connection when module is imported
if __name__ == "__main__":
    if db_connection.connect():
        print("Database module ready!")
        db_connection.close_connection()