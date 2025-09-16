from flask import Flask, jsonify, request, session
from flask_cors import CORS
from database import get_db
from auth import user_auth
from bson import ObjectId
import json
import os
from datetime import datetime
from werkzeug.security import generate_password_hash
from authlib.integrations.flask_client import OAuth

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure session
app.secret_key = os.getenv('SECRET_KEY', 'food-premi-secret-key-change-in-production')
app.config['SESSION_TYPE'] = 'filesystem'
# Frontend origin for post-login redirects (default to local static server)
app.config['FRONTEND_ORIGIN'] = os.getenv('FRONTEND_ORIGIN', 'http://localhost:8080')

# OAuth client configuration
oauth = OAuth(app)
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID', ''),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET', ''),
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/v2/auth',
    api_base_url='https://openidconnect.googleapis.com/v1/',
    client_kwargs={'scope': 'openid email profile'}
)

# Custom JSON encoder to handle ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

# Configure JSON encoder for Flask
app.json_encoder = JSONEncoder

# ID helper to support both ObjectId and string IDs (local DB)
def parse_id(val):
    try:
        return ObjectId(val)
    except Exception:
        return val

# --- Google OAuth ---
@app.route('/api/oauth/google/login')
def google_login():
    # Optional next param for redirecting back to the current page
    session['oauth_next'] = request.args.get('next')
    redirect_uri = request.host_url.rstrip('/') + '/api/oauth/google/callback'
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/api/oauth/google/callback')
def google_callback():
    try:
        token = oauth.google.authorize_access_token()
        resp = oauth.google.get('userinfo')
        info = resp.json()
        email = (info.get('email') or '').lower()
        name = info.get('name') or (email.split('@')[0] if email else 'User')
        picture = info.get('picture') or ''
        sub = info.get('sub')

        db = get_db()
        user_id_str = ''
        role = 'user'
        if db:
            users = db.users
            existing = users.find_one({'email': email}) if email else None
            if existing:
                role = existing.get('role', 'user')
                uid = existing.get('_id')
                user_id_str = str(uid)
                users.update_one({'_id': uid}, {'$set': {
                    'name': name,
                    'avatar': picture,
                    'google_id': sub,
                    'last_login': datetime.utcnow()
                }})
            else:
                doc = {
                    'name': name,
                    'email': email,
                    'password': '',
                    'phone': '',
                    'address': '',
                    'avatar': picture,
                    'google_id': sub,
                    'role': 'user',
                    'created_at': datetime.utcnow(),
                    'last_login': datetime.utcnow(),
                    'is_active': True,
                    'order_count': 0,
                    'total_spent': 0.0
                }
                res = users.insert_one(doc)
                user_id_str = str(res.inserted_id)

        # Session
        session['user_id'] = user_id_str
        session['user_name'] = name
        session['email'] = email
        session['logged_in'] = True
        session['is_admin'] = (role == 'admin')

        # Build small bridge page to sync localStorage then redirect
        next_url = session.pop('oauth_next', None) or (app.config['FRONTEND_ORIGIN'].rstrip('/') + '/index.html')
        safe_name = name.replace('\n',' ').replace('\r',' ')
        safe_email = email.replace('\n',' ').replace('\r',' ')
        safe_pic = picture.replace('\n',' ').replace('\r',' ')
        html = f"""
<!DOCTYPE html>
<html><head><meta charset='utf-8'><title>Signing you in…</title></head>
<body>
<script>
  try {{
    localStorage.setItem('isLoggedIn','true');
    localStorage.setItem('userId', {repr(user_id_str)});
    localStorage.setItem('userName', {repr(safe_name)});
    localStorage.setItem('user', JSON.stringify({{'email': {repr(safe_email)}, 'avatar': {repr(safe_pic)}}}));
  }} catch(e) {{}}
  window.location.href = {repr(next_url)};
</script>
</body></html>
"""
        return html
    except Exception as e:
        return jsonify({'success': False, 'message': f'OAuth error: {str(e)}'}), 400

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
            db.blogs.update_one({'_id': parse_id(post_id)}, {'$set': data})
        return jsonify({'success': True})
    # DELETE
    if db:
        db.blogs.delete_one({'_id': parse_id(post_id)})
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
        'reviews': 0,  # Reviews functionality removed
        'orders': 0,
        'orders_by_status': {}
    }
    if db:
        try:
            counts['orders'] = db.orders.count_documents({})
            statuses = ['placed','accepted','preparing','ready','delivered','cancelled']
            for s in statuses:
                counts['orders_by_status'][s] = db.orders.count_documents({'status': s})
        except Exception:
            pass
    return jsonify({'success': True, 'counts': counts})

# --- Seed initial admin ---
@app.route('/api/seed-admin', methods=['POST'])
def seed_admin():
    db = get_db()
    body = request.get_json() or {}
    email = body.get('email', os.getenv('ADMIN_EMAIL', 'admin@foodpremi.com'))
    name = body.get('name', 'Admin')
    password = body.get('password', os.getenv('ADMIN_SEED_PASSWORD', 'admin123'))
    if db:
        existing = db.users.find_one({'email': email})
        hashed = generate_password_hash(password)
        if existing:
            # Ensure role is admin and update password if provided
            db.users.update_one({'_id': existing['_id']}, {'$set': {'role': 'admin', 'password': hashed, 'name': name}})
        else:
            db.users.insert_one({'email': email, 'name': name, 'password': hashed, 'role': 'admin', 'created_at': datetime.utcnow(), 'is_active': True})
    return jsonify({'success': True, 'email': email})

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
        if not db:
            # Return sample categories for offline mode
            return jsonify({
                "success": True,
                "categories": ["sandwiches", "sprouts", "drinks", "salads", "wraps", "juices", "desserts", "snacks"],
                "message": "Running in offline mode with sample categories"
            })
        
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
    """Add a new menu item (admin only)"""
    try:
        if not session.get('is_admin'):
            return jsonify({'success': False, 'message': 'Admin access required'}), 401
            
        db = get_db()
        if not db:
            return jsonify({'success': False, 'message': 'Database unavailable'}), 503
            
        menu_collection = db.menu_items
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'category', 'description', 'prices']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'message': f'{field} is required'}), 400
        
        # Add metadata
        data['created_at'] = datetime.utcnow()
        data['is_available'] = data.get('is_available', True)
        
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

@app.route('/api/menu/<item_id>', methods=['PUT'])
def update_menu_item(item_id):
    """Update menu item (admin only)"""
    try:
        if not session.get('is_admin'):
            return jsonify({'success': False, 'message': 'Admin access required'}), 401
            
        db = get_db()
        if not db:
            return jsonify({'success': False, 'message': 'Database unavailable'}), 503
            
        menu_collection = db.menu_items
        data = request.get_json()
        
        # Remove fields that shouldn't be updated directly
        data.pop('_id', None)
        data.pop('created_at', None)
        data['updated_at'] = datetime.utcnow()
        
        result = menu_collection.update_one(
            {'_id': parse_id(item_id)},
            {'$set': data}
        )
        
        if result.matched_count == 0:
            return jsonify({'success': False, 'message': 'Item not found'}), 404
        
        return jsonify({
            "success": True,
            "message": "Menu item updated successfully"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/menu/<item_id>', methods=['DELETE'])
def delete_menu_item(item_id):
    """Delete menu item (admin only)"""
    try:
        if not session.get('is_admin'):
            return jsonify({'success': False, 'message': 'Admin access required'}), 401
            
        db = get_db()
        if not db:
            return jsonify({'success': False, 'message': 'Database unavailable'}), 503
            
        menu_collection = db.menu_items
        
        result = menu_collection.delete_one({'_id': parse_id(item_id)})
        
        if result.deleted_count == 0:
            return jsonify({'success': False, 'message': 'Item not found'}), 404
        
        return jsonify({
            "success": True,
            "message": "Menu item deleted successfully"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/menu/<item_id>/toggle', methods=['POST'])
def toggle_menu_item_availability(item_id):
    """Toggle menu item availability (admin only)"""
    try:
        if not session.get('is_admin'):
            return jsonify({'success': False, 'message': 'Admin access required'}), 401
            
        db = get_db()
        if not db:
            return jsonify({'success': False, 'message': 'Database unavailable'}), 503
            
        menu_collection = db.menu_items
        
        item = menu_collection.find_one({'_id': parse_id(item_id)})
        if not item:
            return jsonify({'success': False, 'message': 'Item not found'}), 404
        
        new_availability = not item.get('is_available', True)
        
        menu_collection.update_one(
            {'_id': parse_id(item_id)},
            {'$set': {'is_available': new_availability, 'updated_at': datetime.utcnow()}}
        )
        
        return jsonify({
            "success": True,
            "message": f"Item {'enabled' if new_availability else 'disabled'} successfully",
            "is_available": new_availability
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/offers', methods=['GET', 'POST'])
def manage_offers():
    """Get or create offers"""
    try:
        db = get_db()
        if request.method == 'GET':
            # Get active offers
            if db:
                offers = list(db.offers.find({'is_active': True}).sort('created_at', -1))
            else:
                # Sample offers for offline mode
                offers = [
                    {
                        "_id": "offer1",
                        "title": "Weekend Special",
                        "description": "20% off on all healthy meals",
                        "discount_percentage": 20,
                        "valid_until": "2025-01-20",
                        "is_active": True
                    }
                ]
            return jsonify({'success': True, 'data': offers})
        
        # POST - Create new offer (admin only)
        if not session.get('is_admin'):
            return jsonify({'success': False, 'message': 'Admin access required'}), 401
            
        if not db:
            return jsonify({'success': False, 'message': 'Database unavailable'}), 503
            
        data = request.get_json()
        data['created_at'] = datetime.utcnow()
        data['is_active'] = data.get('is_active', True)
        
        result = db.offers.insert_one(data)
        
        return jsonify({
            "success": True,
            "message": "Offer created successfully",
            "id": str(result.inserted_id)
        }), 201
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/offers/<offer_id>', methods=['PUT', 'DELETE'])
def manage_offer(offer_id):
    """Update or delete offer (admin only)"""
    try:
        if not session.get('is_admin'):
            return jsonify({'success': False, 'message': 'Admin access required'}), 401
            
        db = get_db()
        if not db:
            return jsonify({'success': False, 'message': 'Database unavailable'}), 503
            
        if request.method == 'PUT':
            data = request.get_json()
            data.pop('_id', None)
            data.pop('created_at', None)
            data['updated_at'] = datetime.utcnow()
            
            result = db.offers.update_one(
                {'_id': parse_id(offer_id)},
                {'$set': data}
            )
            
            if result.matched_count == 0:
                return jsonify({'success': False, 'message': 'Offer not found'}), 404
                
            return jsonify({'success': True, 'message': 'Offer updated successfully'})
        
        # DELETE
        result = db.offers.delete_one({'_id': parse_id(offer_id)})
        
        if result.deleted_count == 0:
            return jsonify({'success': False, 'message': 'Offer not found'}), 404
            
        return jsonify({'success': True, 'message': 'Offer deleted successfully'})
        
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
            session['email'] = result['user']['email']
            # Harden admin: set is_admin based on user role
            session['is_admin'] = (result['user'].get('role') == 'admin')
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

# Admin login hardening: only allow admin session if user has admin role
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json() or {}
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Login first'}), 401
    # Allow enabling admin if logged-in user's email matches ADMIN_EMAIL
    allowed_email = os.getenv('ADMIN_EMAIL', '')
    if allowed_email and session.get('email') == allowed_email:
        session['is_admin'] = True
        return jsonify({'success': True, 'message': 'Admin enabled'})
    # Optional dev-only code path controlled by env
    enable_code = os.getenv('ENABLE_ADMIN_CODE', 'false').lower() == 'true'
    if enable_code and data.get('code') and data['code'] == os.getenv('ADMIN_CODE', 'foodpremi-admin'):
        session['is_admin'] = True
        return jsonify({'success': True, 'message': 'Admin enabled via code'})
    # Default: check role already assigned
    if session.get('is_admin'):
        return jsonify({'success': True, 'message': 'Already admin'})
    return jsonify({'success': False, 'message': 'Unauthorized'}), 401

# Orders API: create and list orders
@app.route('/api/orders', methods=['POST', 'GET'])
def orders():
    db = get_db()
    if db is None:
        return jsonify({'success': False, 'message': 'Database unavailable'}), 503

    orders_col = db.orders

    if request.method == 'POST':
        # Require authenticated user
        if not session.get('logged_in'):
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        data = request.get_json() or {}
        items = data.get('items', [])
        total = data.get('total_amount')
        subtotal = data.get('subtotal')
        tax = data.get('tax')
        notes = data.get('notes', '')
        address = data.get('address', '')
        channel = data.get('channel', 'web')

        if not items or total is None:
            return jsonify({'success': False, 'message': 'Invalid order payload'}), 400

        # Basic normalization of items
        norm_items = []
        for it in items:
            norm_items.append({
                'name': it.get('name', ''),
                'size': it.get('size', ''),
                'price': float(it.get('price', 0)),
                'quantity': int(it.get('quantity', 1)),
                'image': it.get('image', '')
            })

        order_doc = {
            'user_id': parse_id(session['user_id']) if session.get('user_id') else None,
            'user_name': session.get('user_name'),
            'user_email': session.get('email'),
            'customer_name': data.get('customer_name') or session.get('user_name'),
            'customer_phone': data.get('customer_phone') or None,
            'items': norm_items,
            'subtotal': float(subtotal) if subtotal is not None else None,
            'tax': float(tax) if tax is not None else None,
            'total_amount': float(total),
            'status': 'placed',
            'channel': channel,
            'notes': notes,
            'address': address,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        res = orders_col.insert_one(order_doc)
        return jsonify({'success': True, 'order_id': str(res.inserted_id)})

    # GET orders: user history or admin (all)
    if session.get('is_admin') and request.args.get('all'):
        cur = orders_col.find().sort('created_at', -1)
    else:
        if not session.get('logged_in'):
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        cur = orders_col.find({'user_id': parse_id(session['user_id'])}).sort('created_at', -1)

    orders_list = []
    for o in cur:
        o['_id'] = str(o['_id'])
        if isinstance(o.get('user_id'), ObjectId):
            o['user_id'] = str(o['user_id'])
        # Normalize datetimes to ISO strings
        if isinstance(o.get('created_at'), datetime):
            o['created_at'] = o['created_at'].isoformat()
        if isinstance(o.get('updated_at'), datetime):
            o['updated_at'] = o['updated_at'].isoformat()
        orders_list.append(o)
    return jsonify({'success': True, 'data': orders_list})

@app.route('/api/orders/<order_id>', methods=['PUT'])
def update_order(order_id):
    # Admin only
    if not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Admin access required'}), 401
    db = get_db()
    if db is None:
        return jsonify({'success': False, 'message': 'Database unavailable'}), 503
    data = request.get_json() or {}
    allowed_status = {'placed', 'accepted', 'preparing', 'ready', 'delivered', 'cancelled'}
    update = {}
    if 'status' in data:
        if data['status'] not in allowed_status:
            return jsonify({'success': False, 'message': 'Invalid status'}), 400
        update['status'] = data['status']
    if 'notes' in data:
        update['notes'] = data['notes']
    if not update:
        return jsonify({'success': False, 'message': 'No valid fields to update'}), 400
    update['updated_at'] = datetime.utcnow()
    res = db.orders.update_one({'_id': parse_id(order_id)}, {'$set': update})
    if res.matched_count == 0:
        return jsonify({'success': False, 'message': 'Order not found'}), 404
    return jsonify({'success': True})

# --- AI Assistant Endpoints ---
# Load environment variables for AI
from dotenv import load_dotenv
load_dotenv()

# In-memory knowledge base for the AI assistant
RESTAURANT_KNOWLEDGE = {
    "menu": """
    Food Premi Menu:

    HEALTHY POWER BOWLS:
    - Quinoa Power Bowl ($12.99) - Organic quinoa, roasted sweet potato, steamed broccoli, chickpeas, avocado, hemp seeds, tahini dressing
    - Mediterranean Bowl ($13.99) - Brown rice, grilled organic chicken, cucumber, cherry tomatoes, feta, olives, hummus
    - Green Goddess Bowl ($11.99) - Kale, spinach, broccoli, edamame, avocado, pumpkin seeds, green goddess dressing

    ORGANIC FRESH SALADS:
    - Farm Fresh Garden Salad ($9.99) - Mixed organic greens, cherry tomatoes, carrots, bell peppers, olive oil vinaigrette
    - Protein Power Salad ($15.99) - Baby spinach, wild salmon, quinoa, walnuts, goat cheese, lemon herb dressing
    - Detox Rainbow Salad ($10.99) - Arugula, shredded beets, carrots, purple cabbage, ginger turmeric dressing

    WHOLESOME MAIN DISHES:
    - Grass-Fed Beef & Roasted Vegetables ($22.99) - 6oz grass-fed beef, roasted vegetables, herb-roasted sweet potatoes
    - Wild-Caught Salmon with Quinoa ($19.99) - Pan-seared salmon, tri-color quinoa, steamed asparagus, lemon dill sauce
    - Free-Range Chicken & Sweet Potato ($17.99) - Herb-marinated chicken, mashed sweet potato, sautéed green beans
    - Plant-Based Buddha Bowl ($14.99) - Lentil-mushroom patty, brown rice, roasted vegetables, tahini sauce

    SUPERFOOD SMOOTHIE BOWLS:
    - Açaí Berry Bowl ($11.99) - Açaí blend, banana, blueberries, granola, coconut flakes, chia seeds
    - Green Machine Bowl ($10.99) - Spinach, mango, pineapple, coconut milk, kiwi, hemp seeds, cacao nibs

    COLD-PRESSED JUICES:
    - Green Detox ($6.99-$8.99) - Kale, spinach, cucumber, celery, green apple, lemon, ginger
    - Immunity Boost ($6.99-$8.99) - Orange, carrot, ginger, turmeric, lemon

    HEALTHY SNACKS:
    - Energy Balls ($4.99) - Dates, almonds, coconut, cacao, chia seeds (pack of 3)
    - Avocado Toast ($7.99) - Organic sourdough, mashed avocado, hemp seeds, everything seasoning

    BEVERAGES:
    - Kombucha ($4.99) - Ginger Turmeric or Mixed Berry flavors
    - Herbal Tea ($2.99-$4.99) - Chamomile, Peppermint, Green Tea, Ginger Lemon
    """,

    "info": """
    Food Premi Restaurant Information:

    HOURS:
    Monday-Friday: 11:00 AM - 9:00 PM
    Saturday: 10:00 AM - 10:00 PM
    Sunday: 10:00 AM - 8:00 PM

    DIETARY ACCOMMODATIONS:
    - Vegan options: Green Goddess Bowl, Plant-Based Buddha Bowl, Açaí Berry Bowl, Green Machine Bowl
    - Gluten-free options: Most bowls and salads (quinoa-based, no wheat)
    - High-protein options: Mediterranean Bowl, Protein Power Salad, Grass-Fed Beef, Wild-Caught Salmon
    - Keto-friendly options: Salads without grains, protein-focused dishes
    - Organic, locally-sourced ingredients throughout menu
    - Raw food options: Most salads, energy balls, cold-pressed juices

    SERVICES:
    - Dine-in service with health-conscious atmosphere
    - Takeout and delivery available
    - Catering for events and corporate meetings
    - Meal prep services for weekly healthy eating
    - Nutritional consultations available

    DAILY SPECIALS:
    - Monday: 20% off all Green Goddess Bowls (Meatless Monday)
    - Tuesday: Buy 2 Cold-Pressed Juices, Get 1 Free
    - Wednesday: Wellness Wednesday - 15% off all meals
    - Thursday: Protein Thursday - Free protein upgrade on any bowl
    - Friday: Fresh Friday - 10% off all salads
    - Weekend: Brunch Special - $2 off smoothie bowls

    PHILOSOPHY:
    We believe in naturally nutritious food using only organic, locally-sourced ingredients.
    All dishes are prepared fresh daily with minimal processing to preserve nutritional value.
    We support local farms and sustainable agriculture practices.
    """
}

@app.route('/api/ask', methods=['POST'])
def ai_ask():
    """AI-powered question answering for restaurant queries"""
    try:
        data = request.get_json()
        question = data.get('question', '')

        if not question:
            return jsonify({'success': False, 'error': 'No question provided'}), 400

        # Import AI components
        from ai.llm_client import chat

        # Create context from knowledge base
        context = RESTAURANT_KNOWLEDGE['menu'] + "\n\n" + RESTAURANT_KNOWLEDGE['info']

        # Create RAG prompt
        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant for Food Premi, a naturally nutritious restaurant. Use the provided context to answer questions about our menu, hours, services, and food philosophy. Be friendly, knowledgeable, and focus on health and nutrition. If someone asks about something not in the context, politely suggest they contact the restaurant directly."
            },
            {
                "role": "user",
                "content": f"Context: {context}\n\nCustomer Question: {question}"
            }
        ]

        # Get response from LLM
        response = chat(messages, temperature=0.2)

        return jsonify({
            'success': True,
            'answer': response,
            'sources': [{'source': 'restaurant_knowledge', 'type': 'menu_info'}],
            'confidence_score': 0.9
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'AI service temporarily unavailable: {str(e)}'
        }), 500

@app.route('/api/ai/status', methods=['GET'])
def ai_status():
    """Check AI system status"""
    try:
        # Test if AI components are available
        from ai.llm_client import ask

        # Quick test
        test_response = ask("Hi", "Respond with just 'OK'")

        return jsonify({
            'success': True,
            'status': 'operational',
            'llm_model': os.getenv('LLM_MODEL', 'llama-3.3-70b-versatile'),
            'message': 'AI assistant is ready to help customers'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
