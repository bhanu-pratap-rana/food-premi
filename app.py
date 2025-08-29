from flask import Flask, jsonify, request, session
from flask_cors import CORS
from database import get_db
from auth import user_auth
from bson import ObjectId
import json
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure session
app.secret_key = os.getenv('SECRET_KEY', 'food-premi-secret-key-change-in-production')
app.config['SESSION_TYPE'] = 'filesystem'

# Custom JSON encoder to handle ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

# Configure JSON encoder for Flask
app.json_encoder = JSONEncoder

# --- Blog CRUD (Mongo) ---
@app.route('/api/blogs', methods=['GET', 'POST'])
def blogs():
    db = get_db()
    if request.method == 'GET':
        posts = list(db.blogs.find().sort('created_at', -1)) if db else []
        return jsonify({'success': True, 'data': posts})
    # admin only create
    data = request.get_json()
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    data['created_at'] = data.get('created_at') or ''
    res = db.blogs.insert_one(data) if db else None
    return jsonify({'success': True, 'id': str(res.inserted_id) if res else 'offline'})

@app.route('/api/blogs/<post_id>', methods=['PUT', 'DELETE'])
def blog_item(post_id):
    db = get_db()
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    if request.method == 'PUT':
        data = request.get_json()
        if db:
            db.blogs.update_one({'_id': ObjectId(post_id)}, {'$set': data})
        return jsonify({'success': True})
    # DELETE
    if db:
        db.blogs.delete_one({'_id': ObjectId(post_id)})
    return jsonify({'success': True})

# Reviews functionality removed - using static ratings in frontend

# --- Admin dashboard summary ---
@app.route('/api/admin/summary')
def admin_summary():
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    db = get_db()
    counts = {
        'users': db.users.count_documents({}) if db else 0,
        'blogs': db.blogs.count_documents({}) if db else 0,
        'reviews': 0  # Reviews functionality removed
    }
    return jsonify({'success': True, 'counts': counts})

# --- Seed initial admin ---
@app.route('/api/seed-admin', methods=['POST'])
def seed_admin():
    db = get_db()
    body = request.get_json() or {}
    email = body.get('email', 'admin@foodpremi.com')
    if db and not db.users.find_one({'email': email}):
        db.users.insert_one({'email': email, 'name': 'Admin', 'password': '', 'role': 'admin'})
    return jsonify({'success': True})

@app.route('/')
def home():
    return jsonify({
        "message": "Welcome to Food Premi API",
        "status": "Active",
        "endpoints": {
            "menu": "/api/menu",
            "categories": "/api/categories",
            "health": "/health"
        }
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        db = get_db()
        if db is not None:
            # Test database connection
            db.command('ping')
            return jsonify({
                "status": "healthy",
                "database": "connected",
                "timestamp": "2025-01-16"
            })
        else:
            return jsonify({
                "status": "healthy",
                "database": "offline_mode",
                "message": "Running without database connection",
                "timestamp": "2025-01-16"
            })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }), 500

@app.route('/api/menu')
def get_menu():
    """Get all menu items"""
    try:
        db = get_db()
        if db is not None:
            menu_collection = db.menu_items
            # Get all menu items and convert ObjectIds to strings
            items = []
            for item in menu_collection.find():
                if '_id' in item:
                    item['_id'] = str(item['_id'])
                items.append(item)
            
            return jsonify({
                "success": True,
                "count": len(items),
                "data": items
            })
        else:
            # Return sample data when offline
            sample_items = [
                {
                    "_id": "sample1",
                    "category": "sandwiches",
                    "name": "Paneer Sandwich",
                    "description": "Fresh paneer with garden vegetables",
                    "image": "https://i.pinimg.com/474x/6b/79/d8/6b79d80d88b53a717843b891f7415d67.jpg",
                    "prices": [
                        {"size": "Small", "price": 60},
                        {"size": "Medium", "price": 80},
                        {"size": "Large", "price": 100}
                    ],
                    "badges": ["Popular"],
                    "is_available": True
                }
            ]
            return jsonify({
                "success": True,
                "count": len(sample_items),
                "data": sample_items,
                "message": "Running in offline mode with sample data"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/menu/<category>')
def get_menu_by_category(category):
    """Get menu items by category"""
    try:
        db = get_db()
        menu_collection = db.menu_items
        
        # Get items by category
        items = list(menu_collection.find({"category": category.lower()}))
        
        return jsonify({
            "success": True,
            "category": category,
            "count": len(items),
            "data": items
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/categories')
def get_categories():
    """Get all available categories"""
    try:
        db = get_db()
        menu_collection = db.menu_items
        
        # Get distinct categories
        categories = menu_collection.distinct("category")
        
        return jsonify({
            "success": True,
            "categories": categories
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/menu', methods=['POST'])
def add_menu_item():
    """Add a new menu item"""
    try:
        db = get_db()
        menu_collection = db.menu_items
        
        # Get data from request
        data = request.get_json()
        
        # Insert the new item
        result = menu_collection.insert_one(data)
        
        return jsonify({
            "success": True,
            "message": "Menu item added successfully",
            "id": str(result.inserted_id)
        }), 201
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/seed-menu', methods=['POST'])
def seed_menu_data():
    """Seed the database with sample menu data"""
    try:
        db = get_db()
        menu_collection = db.menu_items
        
        # Clear existing data
        menu_collection.delete_many({})
        
        # Sample menu data based on your website
        sample_data = [
            {
                "category": "sandwiches",
                "name": "Paneer Wrap with Multigrain Roti",
                "description": "Spiced paneer wrapped in healthy multigrain roti",
                "image": "https://i.pinimg.com/736x/cf/d3/52/cfd352ffce6abbb616838f630fede6d6.jpg",
                "prices": [
                    {"size": "Small", "price": 90},
                    {"size": "Medium", "price": 120},
                    {"size": "Large", "price": 150}
                ],
                "badges": ["New"],
                "is_available": True
            },
            {
                "category": "sprouts",
                "name": "Plain Sprouts",
                "description": "Fresh mixed sprouts with light seasoning",
                "image": "https://i.pinimg.com/736x/a9/17/87/a91787400c7f5859db199a6b847b629d.jpg",
                "prices": [
                    {"size": "Small", "price": 60},
                    {"size": "Medium", "price": 80},
                    {"size": "Large", "price": 100}
                ],
                "badges": ["Healthy"],
                "is_available": True
            },
            {
                "category": "drinks",
                "name": "Green Tea",
                "description": "Antioxidant-rich herbal green tea",
                "image": "https://i.pinimg.com/474x/9b/6e/25/9b6e2552f72dadab5423814c1173b458.jpg",
                "prices": [
                    {"size": "Cup", "price": 20}
                ],
                "badges": ["Healthy"],
                "is_available": True
            }
        ]
        
        # Insert sample data
        result = menu_collection.insert_many(sample_data)
        
        return jsonify({
            "success": True,
            "message": f"Successfully seeded {len(result.inserted_ids)} menu items",
            "inserted_ids": [str(id) for id in result.inserted_ids]
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Authentication Routes
@app.route('/api/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        result = user_auth.register_user(data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Registration error: {str(e)}"
        }), 500

@app.route('/api/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({
                "success": False,
                "message": "Email and password are required"
            }), 400
            
        result = user_auth.login_user(email, password)
        
        if result['success']:
            # Store user info in session
            session['user_id'] = result['user']['user_id']
            session['user_name'] = result['user']['name']
            session['logged_in'] = True
            return jsonify(result), 200
        else:
            return jsonify(result), 401
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Login error: {str(e)}"
        }), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """User logout endpoint"""
    try:
        session.clear()
        return jsonify({
            "success": True,
            "message": "Logged out successfully"
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Logout error: {str(e)}"
        }), 500

@app.route('/api/profile')
def get_profile():
    """Get current user profile"""
    try:
        if not session.get('logged_in'):
            return jsonify({
                "success": False,
                "message": "Not logged in"
            }), 401
            
        user_id = session.get('user_id')
        result = user_auth.get_user_by_id(user_id)
        
        return jsonify(result), 200 if result['success'] else 404
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Profile error: {str(e)}"
        }), 500

@app.route('/api/profile', methods=['PUT'])
def update_profile():
    """Update user profile"""
    try:
        if not session.get('logged_in'):
            return jsonify({
                "success": False,
                "message": "Not logged in"
            }), 401
            
        user_id = session.get('user_id')
        data = request.get_json()
        
        result = user_auth.update_user_profile(user_id, data)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Update error: {str(e)}"
        }), 500

@app.route('/api/auth-status')
def auth_status():
    """Check authentication status"""
    try:
        if session.get('logged_in'):
            return jsonify({
                "logged_in": True,
                "user_id": session.get('user_id'),
                "user_name": session.get('user_name'),
                "is_admin": bool(session.get('is_admin'))
            })
        else:
            return jsonify({"logged_in": False})
    except Exception as e:
        return jsonify({
            "logged_in": False,
            "error": str(e)
        })

# Simple admin login (session flag). In production, secure properly.
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json() or {}
    # Minimal check: if user logged in and email matches configured admin or provided code
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Login first'}), 401
    allowed_email = os.getenv('ADMIN_EMAIL', '')
    if data.get('email') and (allowed_email and data['email'] == allowed_email):
        session['is_admin'] = True
        return jsonify({'success': True, 'message': 'Admin enabled'})
    # dev code path
    if data.get('code') and data['code'] == os.getenv('ADMIN_CODE', 'foodpremi-admin'):
        session['is_admin'] = True
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Unauthorized'}), 401

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)