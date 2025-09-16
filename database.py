from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
import ssl
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import local database fallback
from local_db import get_local_db

class DatabaseConnection:
    def __init__(self):
        # Use environment variable for password, fallback to the provided one
        db_password = os.getenv('DB_PASSWORD', 'b8h9a7n9')
        
        # Working connection string with ServerApi and SSL options
        self.uri = f"mongodb+srv://basant:{db_password}@foodpremi.m4l9uit.mongodb.net/?retryWrites=true&w=majority&appName=foodpremi&tls=true&tlsAllowInvalidCertificates=false"
        self.client = None
        self.db = None
        
    def connect(self):
        """Establish connection to MongoDB using multiple fallback strategies"""

        # Strategy 1: Standard connection with proper SSL
        try:
            print("Strategy 1: Connecting to MongoDB Atlas with standard SSL...")
            self.client = MongoClient(
                self.uri,
                server_api=ServerApi('1'),
                tlsAllowInvalidCertificates=False,
                serverSelectionTimeoutMS=8000,
                connectTimeoutMS=8000,
                socketTimeoutMS=15000
            )

            # Test the connection with ping
            self.client.admin.command('ping')
            print("Successfully connected to MongoDB with standard SSL!")
            self.db = self.client['foodpremi']
            return True

        except Exception as e:
            print(f"Strategy 1 failed: {str(e)[:100]}...")
            if self.client:
                self.client.close()

        # Strategy 2: Relaxed SSL settings
        try:
            print("Strategy 2: Attempting connection with relaxed SSL...")

            # Alternative URI with different SSL approach
            alt_uri = f"mongodb+srv://basant:{os.getenv('DB_PASSWORD', 'b8h9a7n9')}@foodpremi.m4l9uit.mongodb.net/?retryWrites=true&w=majority&appName=foodpremi&ssl=true&authSource=admin"

            self.client = MongoClient(
                alt_uri,
                server_api=ServerApi('1'),
                tlsAllowInvalidCertificates=True,
                serverSelectionTimeoutMS=12000,
                connectTimeoutMS=12000,
                socketTimeoutMS=20000
            )

            self.client.admin.command('ping')
            print("Connected with relaxed SSL settings!")
            self.db = self.client['foodpremi']
            return True

        except Exception as e2:
            print(f"Strategy 2 failed: {str(e2)[:100]}...")
            if self.client:
                self.client.close()

        # Strategy 3: Direct connection with custom SSL context
        try:
            print("Strategy 3: Attempting connection with custom SSL context...")

            # Create a custom SSL context
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            simple_uri = f"mongodb+srv://basant:{os.getenv('DB_PASSWORD', 'b8h9a7n9')}@foodpremi.m4l9uit.mongodb.net/foodpremi"

            self.client = MongoClient(
                simple_uri,
                ssl_context=ssl_context,
                serverSelectionTimeoutMS=15000,
                connectTimeoutMS=15000,
                socketTimeoutMS=25000,
                maxPoolSize=10
            )

            self.client.admin.command('ping')
            print("Connected with custom SSL context!")
            self.db = self.client['foodpremi']
            return True

        except Exception as e3:
            print(f"Strategy 3 failed: {str(e3)[:100]}...")
            if self.client:
                self.client.close()
                self.client = None

        print("All connection strategies failed. Using local database fallback.")
        return False
    
    def get_database(self):
        """Get the database instance"""
        if self.db is None:
            success = self.connect()
            if not success:
                print("Warning: MongoDB unavailable, switching to local database")
                return get_local_db()
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