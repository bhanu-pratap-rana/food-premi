"""
User Authentication Module for Food Premi
Handles user registration, login, and session management
"""

from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from datetime import datetime
import re

class UserAuth:
    def __init__(self):
        self.db = get_db()
        if self.db is not None:
            self.users_collection = self.db.users
        else:
            self.users_collection = None
            print("Warning: Authentication running in offline mode")
        
    def validate_email(self, email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
        
    def validate_phone(self, phone):
        """Validate phone number format"""
        # Indian phone number format
        pattern = r'^[6-9]\d{9}$'
        return re.match(pattern, phone) is not None
        
    def user_exists(self, email):
        """Check if user already exists"""
        if self.users_collection is None:
            return False  # In offline mode, assume user doesn't exist
        return self.users_collection.find_one({"email": email}) is not None
        
    def register_user(self, user_data):
        """Register a new user"""
        try:
            # Check if database is available
            if self.users_collection is None:
                return {"success": False, "message": "Registration unavailable in offline mode"}
            
            # Validate required fields
            required_fields = ['name', 'email', 'password', 'phone']
            for field in required_fields:
                if not user_data.get(field):
                    return {"success": False, "message": f"{field.title()} is required"}
            
            # Validate email format
            if not self.validate_email(user_data['email']):
                return {"success": False, "message": "Invalid email format"}
                
            # Validate phone format
            if not self.validate_phone(user_data['phone']):
                return {"success": False, "message": "Invalid phone number format"}
                
            # Check if user already exists
            if self.user_exists(user_data['email']):
                return {"success": False, "message": "User already exists with this email"}
                
            # Validate password strength
            if len(user_data['password']) < 6:
                return {"success": False, "message": "Password must be at least 6 characters long"}
                
            # Hash password
            hashed_password = generate_password_hash(user_data['password'])
            
            # Create user document
            user_doc = {
                "name": user_data['name'].strip(),
                "email": user_data['email'].lower().strip(),
                "password": hashed_password,
                "phone": user_data['phone'].strip(),
                "address": user_data.get('address', '').strip(),
                "created_at": datetime.utcnow(),
                "last_login": None,
                "is_active": True,
                "order_count": 0,
                "total_spent": 0.0
            }
            
            # Insert user into database
            result = self.users_collection.insert_one(user_doc)
            
            return {
                "success": True, 
                "message": "User registered successfully",
                "user_id": str(result.inserted_id)
            }
            
        except Exception as e:
            return {"success": False, "message": f"Registration failed: {str(e)}"}
            
    def login_user(self, email, password):
        """Authenticate user login"""
        try:
            # Check if database is available
            if self.users_collection is None:
                return {"success": False, "message": "Login unavailable in offline mode"}
            
            # Find user by email
            user = self.users_collection.find_one({"email": email.lower().strip()})
            
            if not user:
                return {"success": False, "message": "Invalid email or password"}
                
            # Check if account is active
            if not user.get('is_active', True):
                return {"success": False, "message": "Account is deactivated"}
                
            # Verify password
            if not check_password_hash(user['password'], password):
                return {"success": False, "message": "Invalid email or password"}
                
            # Update last login
            self.users_collection.update_one(
                {"_id": user['_id']},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            
            # Return user info (excluding password)
            user_info = {
                "user_id": str(user['_id']),
                "name": user['name'],
                "email": user['email'],
                "phone": user['phone'],
                "address": user.get('address', ''),
                "order_count": user.get('order_count', 0),
                "total_spent": user.get('total_spent', 0.0),
                "created_at": user['created_at']
            }
            
            return {
                "success": True,
                "message": "Login successful",
                "user": user_info
            }
            
        except Exception as e:
            return {"success": False, "message": f"Login failed: {str(e)}"}
            
    def get_user_by_id(self, user_id):
        """Get user information by ID"""
        try:
            # Check if database is available
            if self.users_collection is None:
                return {"success": False, "message": "User data unavailable in offline mode"}
            
            user = self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                return {"success": False, "message": "User not found"}
                
            # Return user info (excluding password)
            user_info = {
                "user_id": str(user['_id']),
                "name": user['name'],
                "email": user['email'],
                "phone": user['phone'],
                "address": user.get('address', ''),
                "order_count": user.get('order_count', 0),
                "total_spent": user.get('total_spent', 0.0),
                "created_at": user['created_at'],
                "last_login": user.get('last_login')
            }
            
            return {"success": True, "user": user_info}
            
        except Exception as e:
            return {"success": False, "message": f"Error fetching user: {str(e)}"}
            
    def update_user_profile(self, user_id, update_data):
        """Update user profile information"""
        try:
            # Check if database is available
            if self.users_collection is None:
                return {"success": False, "message": "Profile update unavailable in offline mode"}
            
            # Remove sensitive fields that shouldn't be updated directly
            update_data.pop('password', None)
            update_data.pop('email', None)
            update_data.pop('_id', None)
            
            # Validate phone if provided
            if 'phone' in update_data and not self.validate_phone(update_data['phone']):
                return {"success": False, "message": "Invalid phone number format"}
                
            # Update user document
            result = self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return {"success": True, "message": "Profile updated successfully"}
            else:
                return {"success": False, "message": "No changes made"}
                
        except Exception as e:
            return {"success": False, "message": f"Update failed: {str(e)}"}

# Global auth instance
user_auth = UserAuth()