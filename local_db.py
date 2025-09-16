"""
Local database fallback for Food Premi
Uses file-based storage when MongoDB is unavailable
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class LocalDatabase:
    def __init__(self, data_dir="local_data"):
        self.data_dir = data_dir
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # Initialize collections
        self.collections = {
            'users': LocalCollection(os.path.join(data_dir, 'users.json')),
            'menu_items': LocalCollection(os.path.join(data_dir, 'menu_items.json')),
            'blogs': LocalCollection(os.path.join(data_dir, 'blogs.json')),
            'offers': LocalCollection(os.path.join(data_dir, 'offers.json')),
            'orders': LocalCollection(os.path.join(data_dir, 'orders.json'))
        }
        
        # Seed with sample data if empty
        self._seed_sample_data()
    
    def _seed_sample_data(self):
        """Seed with sample data for immediate functionality"""
        
        # Sample menu items
        if len(self.collections['menu_items'].find()) == 0:
            sample_menu = [
                {
                    "_id": "item_001",
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
                    "is_available": True,
                    "created_at": datetime.utcnow().isoformat()
                },
                {
                    "_id": "item_002",
                    "category": "sprouts",
                    "name": "Mixed Sprouts Salad",
                    "description": "Healthy mix of fresh sprouts with light dressing",
                    "image": "https://i.pinimg.com/736x/a9/17/87/a91787400c7f5859db199a6b847b629d.jpg",
                    "prices": [
                        {"size": "Small", "price": 50},
                        {"size": "Medium", "price": 70},
                        {"size": "Large", "price": 90}
                    ],
                    "badges": ["Healthy", "Fresh"],
                    "is_available": True,
                    "created_at": datetime.utcnow().isoformat()
                },
                {
                    "_id": "item_003",
                    "category": "drinks",
                    "name": "Green Tea",
                    "description": "Antioxidant-rich herbal green tea",
                    "image": "https://i.pinimg.com/474x/9b/6e/25/9b6e2552f72dadab5423814c1173b458.jpg",
                    "prices": [
                        {"size": "Cup", "price": 25}
                    ],
                    "badges": ["Healthy"],
                    "is_available": True,
                    "created_at": datetime.utcnow().isoformat()
                }
            ]
            
            for item in sample_menu:
                self.collections['menu_items'].insert_one(item)
        
        # Sample offers
        if len(self.collections['offers'].find()) == 0:
            sample_offers = [
                {
                    "_id": "offer_001",
                    "title": "Weekend Special",
                    "description": "20% off on all healthy meals",
                    "discount_percentage": 20,
                    "valid_until": "2025-01-31",
                    "is_active": True,
                    "created_at": datetime.utcnow().isoformat()
                }
            ]
            
            for offer in sample_offers:
                self.collections['offers'].insert_one(offer)

    def command(self, command_name, *args, **kwargs):
        """Mock MongoDB command method for compatibility"""
        if command_name == 'ping':
            return {'ok': 1}
        return {'ok': 1, 'result': f'LocalDB command: {command_name}'}

    def list_collection_names(self):
        """Return list of collection names"""
        return list(self.collections.keys())

    def __getattr__(self, name):
        """Allow access to collections as attributes"""
        if name in self.collections:
            return self.collections[name]
        raise AttributeError(f"No collection named '{name}'")

class LocalCollection:
    def __init__(self, file_path):
        self.file_path = file_path
        self._data = self._load_data()
        self._next_id = 1
    
    def _load_data(self) -> List[Dict]:
        """Load data from JSON file"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []
        return []
    
    def _save_data(self):
        """Save data to JSON file"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def _generate_id(self) -> str:
        """Generate a unique ID"""
        while True:
            new_id = f"id_{self._next_id:06d}"
            self._next_id += 1
            if not any(doc.get('_id') == new_id for doc in self._data):
                return new_id
    
    def find_one(self, query: Dict = None) -> Optional[Dict]:
        """Find one document matching the query"""
        if query is None:
            return self._data[0] if self._data else None
        
        for doc in self._data:
            if self._matches_query(doc, query):
                return doc
        return None
    
    def find(self, query: Dict = None) -> 'LocalCollection':
        """Find all documents matching the query - returns LocalCollection for chaining"""
        if query is None:
            filtered_data = self._data[:]
        else:
            filtered_data = [doc for doc in self._data if self._matches_query(doc, query)]

        # Create a new LocalCollection instance with filtered data
        result = LocalCollection(self.file_path)
        result._data = filtered_data
        return result
    
    def insert_one(self, document: Dict):
        """Insert a single document"""
        doc = document.copy()
        if '_id' not in doc:
            doc['_id'] = self._generate_id()
        
        self._data.append(doc)
        self._save_data()
        return _InsertOneResult(doc['_id'])

    def insert_many(self, documents: List[Dict]):
        """Insert multiple documents"""
        ids = []
        for d in documents:
            res = self.insert_one(d)
            ids.append(res.inserted_id)
        return _InsertManyResult(ids)
    
    def update_one(self, query: Dict, update: Dict):
        """Update a single document"""
        for i, doc in enumerate(self._data):
            if self._matches_query(doc, query):
                if '$set' in update:
                    doc.update(update['$set'])
                else:
                    doc.update(update)
                self._save_data()
                return _UpdateResult(1, 1)
        return _UpdateResult(0, 0)
    
    def delete_one(self, query: Dict):
        """Delete a single document"""
        for i, doc in enumerate(self._data):
            if self._matches_query(doc, query):
                del self._data[i]
                self._save_data()
                return _DeleteResult(1)
        return _DeleteResult(0)
    
    def delete_many(self, query: Dict):
        """Delete multiple documents"""
        keep = []
        deleted_count = 0
        for doc in self._data:
            if self._matches_query(doc, query):
                deleted_count += 1
            else:
                keep.append(doc)
        self._data = keep
        self._save_data()
        return _DeleteResult(deleted_count)
    
    def count_documents(self, query: Dict = None) -> int:
        """Count documents matching the query"""
        if query is None:
            return len(self._data)
        return len(self.find(query))
    
    def distinct(self, field: str, query: Dict = None) -> List:
        """Get distinct values for a field"""
        if query:
            docs = [doc for doc in self._data if self._matches_query(doc, query)]
        else:
            docs = self._data

        values = set()
        for doc in docs:
            if field in doc:
                values.add(doc[field])
        return list(values)
    
    def sort(self, field_or_spec, direction: int = 1) -> 'LocalCollection':
        """Sort documents by field (1 for ascending, -1 for descending)"""
        # Handle both MongoDB-style and direct field sorting
        if isinstance(field_or_spec, str):
            field = field_or_spec
        elif isinstance(field_or_spec, list) and len(field_or_spec) > 0:
            # Handle [(field, direction)] format
            field, direction = field_or_spec[0]
        else:
            field = str(field_or_spec)

        reverse = direction == -1
        self._data.sort(key=lambda x: x.get(field, ''), reverse=reverse)
        return self

    def __iter__(self):
        """Make LocalCollection iterable"""
        return iter(self._data)

    def __len__(self):
        """Return length of collection"""
        return len(self._data)
    
    def _matches_query(self, document: Dict, query: Dict) -> bool:
        """Check if document matches query"""
        for key, value in query.items():
            if key not in document:
                return False
            if document[key] != value:
                return False
        return True

# Global instance
local_db = None

def get_local_db():
    """Get local database instance"""
    global local_db
    if local_db is None:
        local_db = LocalDatabase()
    return local_db

# --- PyMongo-like result wrappers ---
class _InsertOneResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id

class _InsertManyResult:
    def __init__(self, inserted_ids):
        self.inserted_ids = inserted_ids

class _UpdateResult:
    def __init__(self, matched_count, modified_count):
        self.matched_count = matched_count
        self.modified_count = modified_count

class _DeleteResult:
    def __init__(self, deleted_count):
        self.deleted_count = deleted_count
